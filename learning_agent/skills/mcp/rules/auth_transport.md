# MCP Auth And Transport Rule

使用场景：
- MCP server 使用 HTTP、SSE、鉴权、会话流或 OAuth metadata。

规则：
- 远程 MCP 优先 Streamable HTTP，配置字段可表达为 transport=http。
- 旧 SSE 是兼容边界，不能假设所有服务都支持。
- GET 可用于监听会话流；Last-Event-ID 可用于恢复；DELETE 可用于关闭 session。
- listen_mcp_stream 是有边界的读取动作，不是后台常驻监听。
- 401、WWW-Authenticate、resource_metadata 和 mcp__server__authenticate 是鉴权恢复线索。
- token 应放在 Authorization: Bearer 或安全 headers 中，不要放进 URL。

关键词：transport=http、Streamable HTTP、SSE、GET、DELETE、Last-Event-ID、401、WWW-Authenticate、resource_metadata、Authorization: Bearer、headers、mcp__server__authenticate、listen_mcp_stream、不会后台常驻监听。
