"""Computer Use MCP v2 工具安装桥接。"""  # 新增代码+ComputerUseMcpV2：说明本文件对应 ClaudeCode setup.ts；如果没有这行代码，工具面构建入口没有同构文件。
from __future__ import annotations  # 新增代码+ComputerUseMcpV2：延迟类型注解解析；如果没有这行代码，类型求值可能提前发生。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.build_tools import computer_use_mcp_tools  # 新增代码+ComputerUseMcpV2：重导出工具 schema 构建函数；如果没有这行代码，setup 层无法提供工具面。


# 新增代码+ClaudeCodeConnectionSetup：函数段开始，复刻 ClaudeCode setup.ts 的职责，把 computer-use MCP server 配置和模型允许工具名一起返回；如果没有这段函数，agent 只能靠散落的旧内置工具发现 Computer Use。
def setup_computer_use_mcp() -> dict[str, object]:
    tools = computer_use_mcp_tools()  # 新增代码+ClaudeCodeConnectionSetup：读取 v2 MCP 包自己声明的工具 schema；如果没有这一行，allowed_tools 可能和真实 tools/list 结果不一致。
    return {  # 新增代码+ClaudeCodeConnectionSetup：返回 ClaudeCode 风格的 setup 结果对象；如果没有这一行，调用方无法一次拿到 MCP 配置和模型白名单。
        "mcp_config": {  # 新增代码+ClaudeCodeConnectionSetup：提供动态 MCP server 配置；如果没有这一层，agent 启动阶段无法像 ClaudeCode 一样把 computer-use 注册进 MCP catalog。
            "computer-use": {  # 新增代码+ClaudeCodeConnectionSetup：固定 server 名为 computer-use；如果没有这一行，工具名前缀会和 `mcp__computer-use__` 不一致。
                "type": "stdio",  # 新增代码+ClaudeCodeConnectionSetup：声明外部协议形态仍是 stdio；如果没有这一行，独立 MCP server 的配置语义不完整。
                "command": "python",  # 新增代码+ClaudeCodeConnectionSetup：声明可独立启动的 Python 命令；如果没有这一行，外部 tools/list 自检无法知道怎么启动 server。
                "args": ["learning_agent/mcp/servers/computer_use_server.py"],  # 新增代码+ClaudeCodeConnectionSetup：指向 v2 stdio wrapper；如果没有这一行，配置会回退到旧 server 或缺少启动入口。
                "scope": "dynamic",  # 新增代码+ClaudeCodeConnectionSetup：标记该 server 是按模式动态加入；如果没有这一行，Computer Use 可能变成普通代码模式常驻工具。
            },  # 新增代码+ClaudeCodeConnectionSetup：computer-use server 配置结束；如果没有这一行，返回结构会语法不完整。
        },  # 新增代码+ClaudeCodeConnectionSetup：mcp_config 配置结束；如果没有这一行，调用方无法区分 server 配置和工具白名单。
        "allowed_tools": [f"mcp__computer-use__{tool['name']}" for tool in tools],  # 新增代码+ClaudeCodeConnectionSetup：把 raw MCP 工具名转换成模型可见前缀名；如果没有这一行，模型可能看到 `left_click` 或旧 `computer_action` 这种错误入口。
    }  # 新增代码+ClaudeCodeConnectionSetup：setup 结果返回结束；如果没有这一行，函数不会把契约结果交给 agent。
# 新增代码+ClaudeCodeConnectionSetup：函数段结束，setup_computer_use_mcp 到此结束；如果没有这个边界说明，用户不容易看出 setup 层只负责发现不负责执行。
