type PlanningPanelProps = { // 新增代码+DesktopGUIPlanningPanel：定义计划协作面板入参；如果没有这段，右侧页签不知道要接收哪个后端 payload。
  payload?: Record<string, unknown>; // 新增代码+DesktopGUIPlanningPanel：保存 planning 总览 payload；如果没有这行，面板只能显示硬编码假数据。
}; // 新增代码+DesktopGUIPlanningPanel：入参类型结束；如果没有这行，TypeScript 类型语法不完整。

function asRecord(value: unknown): Record<string, unknown> { // 新增代码+DesktopGUIPlanningPanel：函数段开始，把未知值安全收敛成对象；如果没有这段，坏 payload 会导致字段读取崩溃。
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {}; // 新增代码+DesktopGUIPlanningPanel：只接受普通对象，否则返回空对象；如果没有这行，数组或 null 会被误当成对象。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，asRecord 到此结束；如果没有这行，类型防护范围不清楚。

function asRecordArray(value: unknown): Array<Record<string, unknown>> { // 新增代码+DesktopGUIPlanningPanel：函数段开始，把未知列表安全收敛成对象数组；如果没有这段，todo/task/peer 列表会信任任意类型。
  return Array.isArray(value) ? value.map((item) => asRecord(item)) : []; // 新增代码+DesktopGUIPlanningPanel：逐项转对象，非数组返回空数组；如果没有这行，map 渲染可能访问非法字段。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，asRecordArray 到此结束；如果没有这行，列表防护范围不清楚。

function asText(value: unknown, fallback = ""): string { // 新增代码+DesktopGUIPlanningPanel：函数段开始，把未知字段转成可显示短文本；如果没有这段，undefined/null 会直接污染 UI。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 新增代码+DesktopGUIPlanningPanel：优先使用非空字符串，否则用兜底；如果没有这行，空字段会让卡片缺标题。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，asText 到此结束；如果没有这行，文本兜底逻辑范围不清楚。

function asNumber(value: unknown, fallback = 0): number { // 新增代码+DesktopGUIPlanningPanel：函数段开始，把未知字段转成数字；如果没有这段，计数可能显示 NaN。
  return typeof value === "number" && Number.isFinite(value) ? value : fallback; // 新增代码+DesktopGUIPlanningPanel：只接受有限数字；如果没有这行，坏计数会污染统计栏。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，asNumber 到此结束；如果没有这行，数字兜底逻辑范围不清楚。

function asBoolean(value: unknown): boolean { // 新增代码+DesktopGUIPlanningPanel：函数段开始，把未知字段转成布尔值；如果没有这段，降级提示无法稳定判断。
  return value === true; // 新增代码+DesktopGUIPlanningPanel：只有明确 true 才算真；如果没有这行，字符串 true 可能被误判。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，asBoolean 到此结束；如果没有这行，布尔兜底逻辑范围不清楚。

function statusClass(status: string): string { // 新增代码+DesktopGUIPlanningPanel：函数段开始，把状态映射到安全 class；如果没有这段，运行中、失败和空态不易扫视。
  if (["failed", "stopped", "unavailable"].includes(status)) { // 新增代码+DesktopGUIPlanningPanel：识别失败或不可用状态；如果没有这行，高风险状态不会突出。
    return "planning-status-danger"; // 新增代码+DesktopGUIPlanningPanel：返回危险状态样式；如果没有这行，失败条目没有视觉提醒。
  } // 新增代码+DesktopGUIPlanningPanel：危险状态分支结束；如果没有这行，条件块语法不完整。
  if (["running", "queued", "pending", "needs_input", "in_progress"].includes(status)) { // 新增代码+DesktopGUIPlanningPanel：识别活动状态；如果没有这行，运行中任务会像普通完成项。
    return "planning-status-active"; // 新增代码+DesktopGUIPlanningPanel：返回活动状态样式；如果没有这行，用户不易发现当前工作。
  } // 新增代码+DesktopGUIPlanningPanel：活动状态分支结束；如果没有这行，条件块语法不完整。
  return "planning-status-muted"; // 新增代码+DesktopGUIPlanningPanel：返回默认状态样式；如果没有这行，函数可能返回 undefined。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，statusClass 到此结束；如果没有这行，状态样式范围不清楚。

function renderEmpty(message: string): JSX.Element { // 新增代码+DesktopGUIPlanningPanel：函数段开始，渲染统一空态；如果没有这段，暂无数据会被误看成坏布局。
  return <p className="planning-empty">{message}</p>; // 新增代码+DesktopGUIPlanningPanel：返回空态文本；如果没有这行，空列表会显示空白。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，renderEmpty 到此结束；如果没有这行，空态渲染范围不清楚。

function renderTodos(todos: Array<Record<string, unknown>>): JSX.Element { // 新增代码+DesktopGUIPlanningPanel：函数段开始，渲染 todo 清单；如果没有这段，todo_read 状态无法肉眼查看。
  const visibleTodos = todos.slice(0, 8); // 新增代码+DesktopGUIPlanningPanel：限制可见 todo 数量；如果没有这行，大清单会撑爆右侧面板。
  return ( // 新增代码+DesktopGUIPlanningPanel：返回 todo 区块 JSX；如果没有这行，函数没有 UI 输出。
    <section className="planning-section"> {/* 新增代码+DesktopGUIPlanningPanel：todo 区块容器；如果没有这一层，标题和条目缺少稳定分区。 */}
      <div className="planning-section-header"> {/* 新增代码+DesktopGUIPlanningPanel：todo 标题行；如果没有这一层，标题和数量无法对齐。 */}
        <h3>Todos</h3> {/* 新增代码+DesktopGUIPlanningPanel：显示 todo 区标题；如果没有这一行，用户不知道列表类型。 */}
        <span>{todos.length}</span> {/* 新增代码+DesktopGUIPlanningPanel：显示 todo 总数；如果没有这一行，截断列表会让用户误判规模。 */}
      </div> {/* 新增代码+DesktopGUIPlanningPanel：todo 标题行结束；如果没有这一层，JSX 结构不完整。 */}
      {visibleTodos.length === 0 ? renderEmpty("暂无 todo 数据。") : visibleTodos.map((todo, index) => { // 新增代码+DesktopGUIPlanningPanel：渲染空态或 todo 条目；如果没有这行，todo 区会空白。
        const status = asText(todo.status, "pending"); // 新增代码+DesktopGUIPlanningPanel：读取 todo 状态；如果没有这行，状态胶囊没有输入。
        return ( // 新增代码+DesktopGUIPlanningPanel：返回单条 todo；如果没有这行，map 回调没有 UI 输出。
          <article className="planning-list-item" key={asText(todo.id, `todo_${index}`)}> {/* 新增代码+DesktopGUIPlanningPanel：todo 条目容器；如果没有这一层，内容、状态和优先级会混在一起。 */}
            <strong>{asText(todo.content, "未命名任务")}</strong> {/* 新增代码+DesktopGUIPlanningPanel：显示 todo 内容；如果没有这一行，todo 没有主体。 */}
            <div className="planning-item-meta"> {/* 新增代码+DesktopGUIPlanningPanel：todo 元信息行；如果没有这一层，状态和优先级不好扫描。 */}
              <span className={statusClass(status)}>{status}</span> {/* 新增代码+DesktopGUIPlanningPanel：显示 todo 状态；如果没有这一行，用户无法判断进度。 */}
              <small>{asText(todo.priority, "medium")}</small> {/* 新增代码+DesktopGUIPlanningPanel：显示 todo 优先级；如果没有这一行，计划排序线索不足。 */}
            </div> {/* 新增代码+DesktopGUIPlanningPanel：todo 元信息行结束；如果没有这一层，JSX 结构不完整。 */}
          </article> // 新增代码+DesktopGUIPlanningPanel：todo 条目结束；如果没有这行，JSX 结构不完整。
        ); // 新增代码+DesktopGUIPlanningPanel：todo 条目返回结束；如果没有这行，map 回调语法不完整。
      })} {/* 新增代码+DesktopGUIPlanningPanel：todo 条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
    </section> // 新增代码+DesktopGUIPlanningPanel：todo 区块结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIPlanningPanel：todo 区块返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，renderTodos 到此结束；如果没有这行，todo 渲染范围不清楚。

function renderTasks(tasks: Array<Record<string, unknown>>): JSX.Element { // 新增代码+DesktopGUIPlanningPanel：函数段开始，渲染子任务列表；如果没有这段，task_list 状态无法肉眼查看。
  const visibleTasks = tasks.slice(0, 8); // 新增代码+DesktopGUIPlanningPanel：限制可见任务数量；如果没有这行，大量历史任务会撑爆右侧面板。
  return ( // 新增代码+DesktopGUIPlanningPanel：返回 task 区块 JSX；如果没有这行，函数没有 UI 输出。
    <section className="planning-section"> {/* 新增代码+DesktopGUIPlanningPanel：task 区块容器；如果没有这一层，任务列表没有分区。 */}
      <div className="planning-section-header"> {/* 新增代码+DesktopGUIPlanningPanel：task 标题行；如果没有这一层，标题和数量无法对齐。 */}
        <h3>Tasks</h3> {/* 新增代码+DesktopGUIPlanningPanel：显示任务区标题；如果没有这一行，用户不知道列表类型。 */}
        <span>{tasks.length}</span> {/* 新增代码+DesktopGUIPlanningPanel：显示任务总数；如果没有这一行，截断列表会让用户误判规模。 */}
      </div> {/* 新增代码+DesktopGUIPlanningPanel：task 标题行结束；如果没有这一层，JSX 结构不完整。 */}
      {visibleTasks.length === 0 ? renderEmpty("暂无任务数据。") : visibleTasks.map((task, index) => { // 新增代码+DesktopGUIPlanningPanel：渲染空态或 task 条目；如果没有这行，task 区会空白。
        const status = asText(task.status, "unknown"); // 新增代码+DesktopGUIPlanningPanel：读取任务状态；如果没有这行，状态胶囊没有输入。
        const title = asText(task.label, asText(task.task_id, `task_${index}`)); // 新增代码+DesktopGUIPlanningPanel：优先用 label，再用 task_id；如果没有这行，任务卡片标题可能为空。
        return ( // 新增代码+DesktopGUIPlanningPanel：返回单个任务卡片；如果没有这行，map 回调没有 UI 输出。
          <article className="planning-list-item" key={asText(task.task_id, `task_${index}`)}> {/* 新增代码+DesktopGUIPlanningPanel：任务条目容器；如果没有这一层，任务字段会散乱。 */}
            <strong>{title}</strong> {/* 新增代码+DesktopGUIPlanningPanel：显示任务标题；如果没有这一行，用户无法定位任务。 */}
            <p>{asText(task.prompt_summary, "无任务目标")}</p> {/* 新增代码+DesktopGUIPlanningPanel：显示任务目标摘要；如果没有这一行，用户不知道任务在做什么。 */}
            <div className="planning-item-meta"> {/* 新增代码+DesktopGUIPlanningPanel：任务元信息行；如果没有这一层，状态、类型和后台标记不好扫描。 */}
              <span className={statusClass(status)}>{status}</span> {/* 新增代码+DesktopGUIPlanningPanel：显示任务状态；如果没有这一行，任务进度不可见。 */}
              <small>{asText(task.kind, "agent")}</small> {/* 新增代码+DesktopGUIPlanningPanel：显示任务类型；如果没有这一行，agent/background 类型不可区分。 */}
              {asBoolean(task.background) ? <small>background</small> : null} {/* 新增代码+DesktopGUIPlanningPanel：显示后台标记；如果没有这一行，后台任务不够显眼。 */}
            </div> {/* 新增代码+DesktopGUIPlanningPanel：任务元信息行结束；如果没有这一层，JSX 结构不完整。 */}
          </article> // 新增代码+DesktopGUIPlanningPanel：任务条目结束；如果没有这行，JSX 结构不完整。
        ); // 新增代码+DesktopGUIPlanningPanel：任务条目返回结束；如果没有这行，map 回调语法不完整。
      })} {/* 新增代码+DesktopGUIPlanningPanel：任务条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
    </section> // 新增代码+DesktopGUIPlanningPanel：task 区块结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIPlanningPanel：task 区块返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，renderTasks 到此结束；如果没有这行，任务渲染范围不清楚。

function renderPeers(peers: Array<Record<string, unknown>>): JSX.Element { // 新增代码+DesktopGUIPlanningPanel：函数段开始，渲染团队 peer 列表；如果没有这段，list_peers 状态无法肉眼查看。
  const visiblePeers = peers.slice(0, 8); // 新增代码+DesktopGUIPlanningPanel：限制可见 peer 数量；如果没有这行，大团队会撑爆右侧面板。
  return ( // 新增代码+DesktopGUIPlanningPanel：返回 peer 区块 JSX；如果没有这行，函数没有 UI 输出。
    <section className="planning-section"> {/* 新增代码+DesktopGUIPlanningPanel：peer 区块容器；如果没有这一层，团队列表没有分区。 */}
      <div className="planning-section-header"> {/* 新增代码+DesktopGUIPlanningPanel：peer 标题行；如果没有这一层，标题和数量无法对齐。 */}
        <h3>Teams</h3> {/* 新增代码+DesktopGUIPlanningPanel：显示团队区标题；如果没有这一行，用户不知道列表类型。 */}
        <span>{peers.length}</span> {/* 新增代码+DesktopGUIPlanningPanel：显示 peer 总数；如果没有这一行，截断列表会让用户误判规模。 */}
      </div> {/* 新增代码+DesktopGUIPlanningPanel：peer 标题行结束；如果没有这一层，JSX 结构不完整。 */}
      {visiblePeers.length === 0 ? renderEmpty("暂无团队数据。") : visiblePeers.map((peer, index) => { // 新增代码+DesktopGUIPlanningPanel：渲染空态或 peer 条目；如果没有这行，团队区会空白。
        const status = asText(peer.status, "idle"); // 新增代码+DesktopGUIPlanningPanel：读取 peer 状态；如果没有这行，状态胶囊没有输入。
        return ( // 新增代码+DesktopGUIPlanningPanel：返回单个 peer 卡片；如果没有这行，map 回调没有 UI 输出。
          <article className="planning-list-item" key={asText(peer.peer_id, `peer_${index}`)}> {/* 新增代码+DesktopGUIPlanningPanel：peer 条目容器；如果没有这一层，peer 字段会散乱。 */}
            <strong>{asText(peer.name, "peer")}</strong> {/* 新增代码+DesktopGUIPlanningPanel：显示 peer 名称；如果没有这一行，团队成员不可读。 */}
            <p>{asText(peer.notes, asText(peer.bound_task_id, "暂无备注"))}</p> {/* 新增代码+DesktopGUIPlanningPanel：显示备注或绑定任务；如果没有这一行，peer 缺上下文。 */}
            <div className="planning-item-meta"> {/* 新增代码+DesktopGUIPlanningPanel：peer 元信息行；如果没有这一层，角色、状态和消息数不好扫描。 */}
              <span className={statusClass(status)}>{status}</span> {/* 新增代码+DesktopGUIPlanningPanel：显示 peer 状态；如果没有这一行，团队成员状态不可见。 */}
              <small>{asText(peer.role, "peer")}</small> {/* 新增代码+DesktopGUIPlanningPanel：显示 peer 角色；如果没有这一行，分工不可见。 */}
              <small>{asNumber(peer.pending_message_count, 0)} pending</small> {/* 新增代码+DesktopGUIPlanningPanel：显示待处理消息数；如果没有这一行，协作待办不明显。 */}
            </div> {/* 新增代码+DesktopGUIPlanningPanel：peer 元信息行结束；如果没有这一层，JSX 结构不完整。 */}
          </article> // 新增代码+DesktopGUIPlanningPanel：peer 条目结束；如果没有这行，JSX 结构不完整。
        ); // 新增代码+DesktopGUIPlanningPanel：peer 条目返回结束；如果没有这行，map 回调语法不完整。
      })} {/* 新增代码+DesktopGUIPlanningPanel：peer 条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
    </section> // 新增代码+DesktopGUIPlanningPanel：peer 区块结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIPlanningPanel：peer 区块返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，renderPeers 到此结束；如果没有这行，团队渲染范围不清楚。

function renderMessages(messages: Array<Record<string, unknown>>): JSX.Element { // 新增代码+DesktopGUIPlanningPanel：函数段开始，渲染 peer 消息列表；如果没有这段，read_peer_messages 状态无法肉眼查看。
  const visibleMessages = messages.slice(0, 6); // 新增代码+DesktopGUIPlanningPanel：限制可见消息数量；如果没有这行，大 inbox 会撑爆右侧面板。
  return ( // 新增代码+DesktopGUIPlanningPanel：返回消息区块 JSX；如果没有这行，函数没有 UI 输出。
    <section className="planning-section"> {/* 新增代码+DesktopGUIPlanningPanel：消息区块容器；如果没有这一层，消息列表没有分区。 */}
      <div className="planning-section-header"> {/* 新增代码+DesktopGUIPlanningPanel：消息标题行；如果没有这一层，标题和数量无法对齐。 */}
        <h3>Peer Messages</h3> {/* 新增代码+DesktopGUIPlanningPanel：显示消息区标题；如果没有这一行，用户不知道列表类型。 */}
        <span>{messages.length}</span> {/* 新增代码+DesktopGUIPlanningPanel：显示消息总数；如果没有这一行，截断列表会让用户误判规模。 */}
      </div> {/* 新增代码+DesktopGUIPlanningPanel：消息标题行结束；如果没有这一层，JSX 结构不完整。 */}
      {visibleMessages.length === 0 ? renderEmpty("暂无消息数据。") : visibleMessages.map((message, index) => { // 新增代码+DesktopGUIPlanningPanel：渲染空态或消息条目；如果没有这行，消息区会空白。
        const status = asText(message.status, "pending"); // 新增代码+DesktopGUIPlanningPanel：读取消息状态；如果没有这行，ack 状态不可见。
        return ( // 新增代码+DesktopGUIPlanningPanel：返回单条消息；如果没有这行，map 回调没有 UI 输出。
          <article className="planning-list-item" key={asText(message.message_id, `message_${index}`)}> {/* 新增代码+DesktopGUIPlanningPanel：消息条目容器；如果没有这一层，消息字段会散乱。 */}
            <strong>{asText(message.sender, "peer")} → {asText(message.peer_name, "peer")}</strong> {/* 新增代码+DesktopGUIPlanningPanel：显示发送方和 peer；如果没有这一行，用户不知道消息归属。 */}
            <p>{asText(message.content_summary, "空消息")}</p> {/* 新增代码+DesktopGUIPlanningPanel：显示消息摘要；如果没有这一行，消息没有主体内容。 */}
            <div className="planning-item-meta"> {/* 新增代码+DesktopGUIPlanningPanel：消息元信息行；如果没有这一层，状态和时间不好扫描。 */}
              <span className={statusClass(status)}>{status}</span> {/* 新增代码+DesktopGUIPlanningPanel：显示消息状态；如果没有这一行，pending/ack 不可见。 */}
              <small>{asText(message.created_at, "no time")}</small> {/* 新增代码+DesktopGUIPlanningPanel：显示创建时间；如果没有这一行，消息时间线不可见。 */}
            </div> {/* 新增代码+DesktopGUIPlanningPanel：消息元信息行结束；如果没有这一层，JSX 结构不完整。 */}
          </article> // 新增代码+DesktopGUIPlanningPanel：消息条目结束；如果没有这行，JSX 结构不完整。
        ); // 新增代码+DesktopGUIPlanningPanel：消息条目返回结束；如果没有这行，map 回调语法不完整。
      })} {/* 新增代码+DesktopGUIPlanningPanel：消息条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
    </section> // 新增代码+DesktopGUIPlanningPanel：消息区块结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIPlanningPanel：消息区块返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，renderMessages 到此结束；如果没有这行，消息渲染范围不清楚。

function renderTools(tools: Array<Record<string, unknown>>): JSX.Element { // 新增代码+DesktopGUIPlanningPanel：函数段开始，渲染计划工具可用性；如果没有这段，用户看不到 GUI 复用了哪些 agent 工具。
  const visibleTools = tools.slice(0, 10); // 新增代码+DesktopGUIPlanningPanel：限制可见工具数量；如果没有这行，工具列表会压过状态数据。
  return ( // 新增代码+DesktopGUIPlanningPanel：返回工具区块 JSX；如果没有这行，函数没有 UI 输出。
    <section className="planning-section"> {/* 新增代码+DesktopGUIPlanningPanel：工具区块容器；如果没有这一层，工具可用性没有分区。 */}
      <div className="planning-section-header"> {/* 新增代码+DesktopGUIPlanningPanel：工具标题行；如果没有这一层，标题和数量无法对齐。 */}
        <h3>Tools</h3> {/* 新增代码+DesktopGUIPlanningPanel：显示工具区标题；如果没有这一行，用户不知道列表类型。 */}
        <span>{tools.length}</span> {/* 新增代码+DesktopGUIPlanningPanel：显示工具总数；如果没有这一行，截断列表会让用户误判规模。 */}
      </div> {/* 新增代码+DesktopGUIPlanningPanel：工具标题行结束；如果没有这一层，JSX 结构不完整。 */}
      {visibleTools.length === 0 ? renderEmpty("暂无工具数据。") : visibleTools.map((tool, index) => { // 新增代码+DesktopGUIPlanningPanel：渲染空态或工具条目；如果没有这行，工具区会空白。
        const status = asText(tool.status, asBoolean(tool.available) ? "available" : "unavailable"); // 新增代码+DesktopGUIPlanningPanel：读取工具状态；如果没有这行，可用性不可见。
        const reason = asText(tool.safe_unavailable_reason, ""); // 新增代码+DesktopGUIPlanningPanel：读取不可用原因；如果没有这行，缺工具时没有解释。
        return ( // 新增代码+DesktopGUIPlanningPanel：返回单个工具条目；如果没有这行，map 回调没有 UI 输出。
          <article className="planning-tool-item" key={asText(tool.name, `tool_${index}`)}> {/* 新增代码+DesktopGUIPlanningPanel：工具条目容器；如果没有这一层，工具字段会散乱。 */}
            <strong>{asText(tool.name, "tool")}</strong> {/* 新增代码+DesktopGUIPlanningPanel：显示工具名；如果没有这一行，用户不知道是哪条能力。 */}
            <div className="planning-item-meta"> {/* 新增代码+DesktopGUIPlanningPanel：工具元信息行；如果没有这一层，状态和权限不好扫描。 */}
              <span className={statusClass(status)}>{status}</span> {/* 新增代码+DesktopGUIPlanningPanel：显示工具状态；如果没有这一行，可用性不可见。 */}
              <small>{asText(tool.category, "planning")}</small> {/* 新增代码+DesktopGUIPlanningPanel：显示能力分组；如果没有这一行，planning/delegation 不可区分。 */}
              <small>{asBoolean(tool.read_only) ? "read" : "write"}</small> {/* 新增代码+DesktopGUIPlanningPanel：显示读写性质；如果没有这一行，mutation 风险不可见。 */}
            </div> {/* 新增代码+DesktopGUIPlanningPanel：工具元信息行结束；如果没有这一层，JSX 结构不完整。 */}
            {reason ? <p>{reason}</p> : null} {/* 新增代码+DesktopGUIPlanningPanel：显示不可用原因；如果没有这一行，缺工具时用户只看到 unavailable。 */}
          </article> // 新增代码+DesktopGUIPlanningPanel：工具条目结束；如果没有这行，JSX 结构不完整。
        ); // 新增代码+DesktopGUIPlanningPanel：工具条目返回结束；如果没有这行，map 回调语法不完整。
      })} {/* 新增代码+DesktopGUIPlanningPanel：工具条件渲染结束；如果没有这行，JSX 表达式不完整。 */}
    </section> // 新增代码+DesktopGUIPlanningPanel：工具区块结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIPlanningPanel：工具区块返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，renderTools 到此结束；如果没有这行，工具渲染范围不清楚。

export function PlanningPanel({ payload = {} }: PlanningPanelProps): JSX.Element { // 新增代码+DesktopGUIPlanningPanel：函数段开始，渲染计划协作控制中心；如果没有这段，右侧 GUI 无法查看 todo/task/team 状态。
  const panel = asRecord(payload); // 新增代码+DesktopGUIPlanningPanel：收敛 payload；如果没有这行，坏数据会让面板崩溃。
  const todos = asRecordArray(panel.todos); // 新增代码+DesktopGUIPlanningPanel：读取 todo 列表；如果没有这行，todo 区无法渲染。
  const tasks = asRecordArray(panel.tasks); // 新增代码+DesktopGUIPlanningPanel：读取 task 列表；如果没有这行，任务区无法渲染。
  const peers = asRecordArray(panel.peers); // 新增代码+DesktopGUIPlanningPanel：读取 peer 列表；如果没有这行，团队区无法渲染。
  const messages = asRecordArray(panel.peer_messages); // 新增代码+DesktopGUIPlanningPanel：读取 peer 消息；如果没有这行，消息区无法渲染。
  const tools = asRecordArray(panel.tools); // 新增代码+DesktopGUIPlanningPanel：读取工具摘要；如果没有这行，工具区无法渲染。
  const degraded = asBoolean(panel.status_degraded); // 新增代码+DesktopGUIPlanningPanel：读取降级状态；如果没有这行，读取失败不会提示。
  const safeError = asText(panel.safe_error, "计划协作状态暂时不可读。"); // 新增代码+DesktopGUIPlanningPanel：读取脱敏错误；如果没有这行，降级提示可能空白。
  const availableToolCount = asNumber(panel.available_tool_count, tools.filter((tool) => asBoolean(tool.available)).length); // 新增代码+DesktopGUIPlanningPanel：读取可用工具数；如果没有这行，标题统计不稳定。
  const toolCount = asNumber(panel.tool_count, tools.length); // 新增代码+DesktopGUIPlanningPanel：读取工具总数；如果没有这行，标题统计不稳定。
  return ( // 新增代码+DesktopGUIPlanningPanel：返回 planning 面板 JSX；如果没有这行，组件没有 UI 输出。
    <section className="planning-panel" aria-label="计划协作控制中心"> {/* 新增代码+DesktopGUIPlanningPanel：面板根容器；如果没有这一层，样式和验收无法稳定定位。 */}
      <div className="planning-header"> {/* 新增代码+DesktopGUIPlanningPanel：标题行；如果没有这一层，标题和工具统计会混乱。 */}
        <div> {/* 新增代码+DesktopGUIPlanningPanel：标题文本容器；如果没有这一层，标题和说明无法垂直排列。 */}
          <h2>计划协作</h2> {/* 新增代码+DesktopGUIPlanningPanel：显示面板标题；如果没有这一行，用户不知道当前页签用途。 */}
          <p>复用 todo、task registry 和 team registry 的只读状态</p> {/* 新增代码+DesktopGUIPlanningPanel：说明数据来源；如果没有这一行，用户无法确认 GUI 没有重写计划系统。 */}
        </div> {/* 新增代码+DesktopGUIPlanningPanel：标题文本容器结束；如果没有这一层，JSX 结构不完整。 */}
        <span>{availableToolCount}/{toolCount} tools</span> {/* 新增代码+DesktopGUIPlanningPanel：显示工具接入数；如果没有这一行，用户无法快速判断能力覆盖。 */}
      </div> {/* 新增代码+DesktopGUIPlanningPanel：标题行结束；如果没有这一层，JSX 结构不完整。 */}
      <div className="planning-summary"> {/* 新增代码+DesktopGUIPlanningPanel：摘要行；如果没有这一层，todo/task/peer/message 统计缺少固定位置。 */}
        <span>{asNumber(panel.todo_count, todos.length)} todos</span> {/* 新增代码+DesktopGUIPlanningPanel：显示 todo 数量；如果没有这一行，计划规模不可见。 */}
        <span>{asNumber(panel.active_task_count, 0)} active tasks</span> {/* 新增代码+DesktopGUIPlanningPanel：显示活动任务数量；如果没有这一行，后台工作不可见。 */}
        <span>{asNumber(panel.peer_count, peers.length)} peers</span> {/* 新增代码+DesktopGUIPlanningPanel：显示 peer 数量；如果没有这一行，团队规模不可见。 */}
        <span>{asNumber(panel.pending_peer_message_count, 0)} pending messages</span> {/* 新增代码+DesktopGUIPlanningPanel：显示待确认消息数；如果没有这一行，协作待办不可见。 */}
      </div> {/* 新增代码+DesktopGUIPlanningPanel：摘要行结束；如果没有这一层，JSX 结构不完整。 */}
      {degraded ? <p className="planning-warning">{safeError}</p> : null} {/* 新增代码+DesktopGUIPlanningPanel：显示降级提示；如果没有这一行，读取失败会被误认为正常空态。 */}
      <div className="planning-grid"> {/* 新增代码+DesktopGUIPlanningPanel：内容网格；如果没有这一层，各 section 会缺少稳定间距。 */}
        {renderTodos(todos)} {/* 新增代码+DesktopGUIPlanningPanel：渲染 todo 区；如果没有这一行，计划清单不可见。 */}
        {renderTasks(tasks)} {/* 新增代码+DesktopGUIPlanningPanel：渲染任务区；如果没有这一行，子任务状态不可见。 */}
        {renderPeers(peers)} {/* 新增代码+DesktopGUIPlanningPanel：渲染团队区；如果没有这一行，peer 状态不可见。 */}
        {renderMessages(messages)} {/* 新增代码+DesktopGUIPlanningPanel：渲染消息区；如果没有这一行，peer inbox 不可见。 */}
        {renderTools(tools)} {/* 新增代码+DesktopGUIPlanningPanel：渲染工具区；如果没有这一行，计划/委派工具可用性不可见。 */}
      </div> {/* 新增代码+DesktopGUIPlanningPanel：内容网格结束；如果没有这一层，JSX 结构不完整。 */}
    </section> // 新增代码+DesktopGUIPlanningPanel：面板根容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIPlanningPanel：组件返回结束；如果没有这行，函数语法不完整。
} // 新增代码+DesktopGUIPlanningPanel：函数段结束，PlanningPanel 到此结束；如果没有这行，面板职责范围不清楚。
