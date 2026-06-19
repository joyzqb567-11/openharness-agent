# Experience

## 2026-06-19 Computer Use complex GUI task stage-runtime lesson

Computer Use complex GUI tasks must not rely on primitive tool-loop convergence. The stable design is generic stage planning, stage-boundary observation, batch execution, and stage verification. App-specific samples are acceptance fixtures, not architecture.

- 经验：画图、文本编辑、浏览、表单、多软件协作这类任务不能靠“模型每轮自己想下一步原子动作”自然收敛；否则很容易只完成一笔、一行或一个窗口动作，就把 `Next desktop action` 当成最终回答。
- 做法：先在规划层生成 `DesktopTaskPlan` 和 `StagePlan`，再由观察层只在阶段边界确认状态，由执行层一次性批量执行该阶段动作，最后由验证层判断该阶段是否真的完成。
- 边界：代表性验收可以使用 Paint、Notepad、浏览器等本机软件，但这些名字只能出现在 acceptance fixture、别名发现和日志证据里，不能变成生产运行时的专用控制分支。
- 门禁：最终回答门禁只能作为兜底。真正减少失败和耗时的核心，是阶段规划、阶段观察、批执行和阶段验证，而不是继续加长提示词或让模型反复输入 `Y`、反复 observe。

## 2026-05-28 长回答验收断言经验

- 经验：真实终端验收不能只用 `answer_preview` 判断最终回答是否包含关键字段，因为长回答很容易在 500 字预览处截断。
- 建议：事件 payload 同时保留 `answer_preview` 和 `answer_text`；`answer_preview` 用于快速看摘要，`answer_text` 用于机器断言。
- 建议：controller 需要兼容旧事件，若没有 `answer_text` 再回退到 `answer_preview`，避免历史 run 证据无法读取。
- 建议：当工具日志和最终回答日志都显示成功，而 controller 只在 event answer check 失败时，优先排查事件预览截断或事件字段不足，不要先怀疑浏览器动作失败。

## 2026-05-28 真实浏览器自然查询识别经验

- 经验：公开查询任务不能只匹配“查询/搜索”这类动词，用户经常会说“某网站的视频、评论最多、有哪些、排行、介绍”等问句；这类表达也必须进入真实浏览器客户模式，否则会重新出现多次 `y/N`。
- 建议：修复此类问题时必须用用户截图里的原始短 prompt 做红灯测试，再跑真实可见终端验收并检查 `permission_sent_count=0`。
- 建议：已经启动的旧 `start_oauth_agent.bat` 进程不会热加载代码，权限体验类修复完成后要提醒用户重启终端再复测。

## 2026-06-04 Windows workspace replace/unlink denied 经验

- 经验：在当前 Codex/Windows workspace 中，普通 `Path.write_text()` 可能成功，但 `os.replace()`、`Path.unlink()` 这类 rename/delete 操作可能稳定返回 `WinError 5`。
- 建议：遇到状态文件落盘失败时，不要只看 ACL；要分别用最小探针验证 direct write、replace 和 unlink，因为这三类权限表现可能不同。
- 建议：状态文件写入应首选 atomic replace，但要给受限 workspace 准备 PermissionError 兜底路径；兜底只能在 replace 重试耗尽后启用，避免正常环境退化。
- 建议：Windows 跨进程锁不要依赖“创建 mutex 文件再删除”释放锁；优先使用 `msvcrt.locking` 这类句柄级锁，锁文件可以留下但不代表锁仍被占用。
- 建议：真实 CLI 或可见终端验收被状态落盘卡住时，要同时检查 `FileLock.__exit__`，因为业务异常之后的锁清理异常可能遮蔽原始错误。

---

## 2026-06-05 Phase97 Notepad Live Edit Lessons

- Fake sender 接受某个事件形状，不等于真实 Windows sender 支持该事件。真实路径必须至少有一个测试覆盖真实 sender 的分发分支，或者跑真实 CLI 验证。
- Windows 11 Notepad 可能是单实例/转发启动，`subprocess.Popen(...).pid` 不一定等于真实窗口 pid。对 Notepad 目标身份不能只用 launcher pid；应结合唯一文件名、启动前 baseline、window_id 和安全复核。
- Notepad 标题只显示文件名，不显示完整路径。真实验收文件名应带唯一后缀，否则旧同名窗口会污染 baseline。
- 对 Notepad 长文本逐字符 `SendInput` 可能丢字或重复字。固定受控文本验收更适合“临时剪贴板粘贴 + 恢复剪贴板 + 保存验证”，并且必须保证报告不泄露正文。
- 64 位 Windows 的剪贴板句柄和内存指针必须显式设置 `ctypes` 的 `restype/argtypes`，否则句柄截断会导致 access violation。

---

---
## 2026-06-06 Computer Use Default Route Must Be Rechecked From Source

- Experience: project memory can become stale; before judging `/computer use --full`, inspect `LearningAgent._desktop_task_runtime_for_current_run()` and the injected `UniversalDesktopExecutionLoopAdapter` arguments directly.
- Experience: the normal user path must not enable object-specific Paint bridges. Arbitrary drawing/control should be solved by a generic planner plus observe-plan-act-verify loop, not by adding more subject-specific controllers.
- Experience: a passing legacy Paint/Pikachu direct loop test is only fixture evidence; it is not production maturity evidence for universal Computer Use.
## 2026-06-06 Computer Use 能力分层经验

- `/computer use --full` 的成熟度必须分层判断：特例绘图、真实观察、动作 DSL 展开、受控物理派发、真实应用启动、窗口激活、视觉规划、观察纠偏、最终任务验证是不同能力，不能因为其中一层通过就宣称整体成熟。
- 单元测试中的真实派发形状必须用 safe fake backend，不能让自动化回归意外移动用户真实鼠标键盘；真实可见终端验收才允许触发现实桌面。
- 受控/真实 sender 不一定维护 recording sender 的 `low_level_events` 列表，顶层事件数应优先读取 sender 返回的 `low_level_event_count`，否则真实动作会被误报为 0。
- 后续修复任意绘图能力时，应优先接通通用 real launch、window activation、visual planner、observe-correct loop，而不是继续新增猫、狗、房子等硬编码画图对象。

## 2026-06-06 Agent-Owned Launch 验收经验

- 经验：真实物理派发通过，不等于 agent 自己打开了目标软件；验收必须同时检查 `real_launch_performed=true`、`owned_process_registered=true`、`visible_window_verified=true` 和目标窗口 pid。
- 经验：单元测试里的默认 full 路径不能真的启动 Paint；真实桌面副作用只允许在可见终端验收场景中发生，自动化回归要用 safe fake launch backend 和 fake window probe。
- 经验：`/computer stop` 的 cleanup 输出也需要事实复核；如果 `Get-Process` 仍能看到 agent-owned pid，就不能把 `residual_owned_process=false` 当成可信结论。

## 2026-06-06 Visual Planner 验收经验

- 经验：真实 Paint 窗口的 observation rect 不一定包含 `width/height`，planner 必须从 `right-left` 和 `bottom-top` 推导尺寸，否则会把动作规划到错误区域。
- 经验：`visual_planner_connected=true` 只证明接口接入，不证明语义绘图成熟；必须看最终截图是否符合自然语言目标。
- 经验：验收 prompt 应该使用真实用户习惯，例如先输入 `/computer use --full`，再输入 `请使用本地电脑的画图软件画一个房子。`，不能使用内部确认 token 或开发者快捷命令替代。
- 经验：如果截图只显示通用形状或错误对象，应把结论记录为“真实路线已打通但 planner 不成熟”，不能为了推进而说任意绘图已完成。

## 2026-06-06 Visual Semantic Planner 经验

- 经验：只把 `prompt_signature` 传给 planner 会保护隐私，但也会让 planner 不知道用户到底想画什么；正确做法是抽取脱敏结构化意图，例如 `visual_subject_hint=house`，同时保持 `raw_prompt_included=false`。
- 经验：真实验收不应只检查 `visual_planner_used=true`，还要检查动作证据里的 `semantic_role`，否则“通用脸”仍可能被误判成语义绘图成功。
- 经验：新增语义能力时应放在独立 planner 模块里，不要继续把每个对象的笔画都堆进 `Phase120VisualTaskPlanner.plan()`。
- 经验：阶段性支持 house 不等于任意绘图成熟，成熟度字段应继续保守显示 `visual_planner_mature=false`。
## 2026-06-06 Computer Use full 反复误判经验

- 不能只看“窗口截图存在”就判断模型能看屏幕；必须确认截图以模型可读的 image block/data URL 进入下一轮模型输入。
- 不能只看“Paint 窗口存在”就判断 agent 打开了软件；必须确认工具结果里有 `launch_app`、`session_ready=true`、`target_window`、`agent-owned` 或等价自有窗口证据。
- 对本机应用任务，真实验收必须区分用户旧窗口和 agent-owned 新窗口；否则会把用户手动打开软件误判成 agent 成功启动软件。
## 2026-06-06 16:59 经验：Computer Use launch_app 不能优先信任 app_name
- 模型在多轮真实桌面任务中可能把任务说明混入 `app_name`，即使同时给出干净的 `target_app/app/target`。
- 以后设计工具 schema 或 controller 入口时，应把更结构化、更短、更像别名的字段优先级放在前面，并把自然语言句子标点作为污染信号。
- 真实桌面能力的验收不能只看“有 low_level_event_count”，还必须确认动作绑定的是 agent-owned 目标窗口，并且最终回答能引用真实截图证据。

## 2026-06-06 17:12 经验：所有 launch_app 目标字段都可能被污染
- 不能假设 `target_app` 比 `app_name` 更干净；真实模型可能把任务说明塞进任何一个目标字段。
- controller 应把每个候选都当作不可信输入，逐个清洗，跳过污染字段，直到找到干净别名。
- GUI 绘图这类真实验收会受模型响应速度影响，场景超时要覆盖完整 observe-plan-act-final 周期，否则功能实际完成也可能被验收器提前判失败。

## 2026-06-07 经验：Computer Use maturity 不能用旧单字段代替源码事实
- 判断 `/computer use --full` 当前设计时，不能只看 `visual_planner_mature=false`、`paint_pikachu_visible_terminal_acceptance=false` 或旧验收名字；这些字段可能只是旧 fixture 或单层能力边界。
- 成熟度矩阵必须同时输出“模型主循环语义规划、工具 schema 可见、截图 image block 回流、discover/launch_app/drag_path 工具面、旧 Paint fixture 降级、默认生产路线不是 Paint 桥”这类源码可验证事实。
- 后续如果用户质疑 Computer Use 能力，先读 `core/agent.py`、`tools/schemas.py`、`full_maturity_matrix.py` 和真实 terminal run，再下判断；不要用压缩后的旧记忆替代源码证据。
## 2026-06-07 Phase128：Computer Use maturity 必须分层，不能让视觉质量缺口否定通用主循环

- 经验：`computer maturity` 只能汇总源码和验收证据，不能用单个旧字段代表全部能力。
- 经验：看到 `visual_planner_mature=false` 时，必须解释为“视觉质量验收/纠偏验收未成熟”，不能解释为“模型主循环不会理解用户意图”或“通用软件控制不可用”。
- 经验：顶层矩阵必须同时显示 `generic_app_control_foundation_ready`、`model_loop_computer_use_foundation_ready`、`visual_quality_acceptance_passed`、`visual_correction_acceptance_passed`，这样后续修视觉质量时不会误改通用软件控制链。
- 经验：首轮 Computer Use 工具面应保留 `computer_discover` 和 `computer_action`，这与 ClaudeCode 风格“先发现工具/应用清单，再选择工具”的设计一致；旧测试若要求只暴露 `computer_action`，应视为旧口径。

## 2026-06-07 经验：Computer Use maturity 必须有全量源码结构审计和诚实边界

- 经验：当用户质疑 `/computer use --full` 是否成熟时，不能只读文档、旧记忆或少数主链路文件；至少要让 maturity 矩阵枚举 `learning_agent/computer_use/*.py` 全量源码，并输出文件数量、AST 可解析状态、架构层映射和主链路文件存在性。
- 经验：源码架构审计必须同时说明“能证明什么”和“不能证明什么”；`computer_use_source_audit_static_only=true` 与 `computer_use_source_audit_semantic_complete=false` 这类边界字段很重要，避免把静态结构审计误当真实桌面执行质量证明。
- 经验：旧代表样例文件（Paint/Pikachu/Notepad/representative）不一定要立刻删除，但必须被显式归类和扫描，不能再让它们冒充 `/computer use --full` 的通用成熟能力。
- 经验：CLI token 不应该继续堆成超长单行 f-string；成熟度矩阵字段会持续增长，应该使用字段列表拼接，减少后续误接、漏接和上下文压缩后的维护风险。
## 2026-06-07 Phase130 Runtime Reachability Lesson
- 后续评估 Computer Use 源码时，不要把目录枚举结果等同于运行时核心链路。
- 必须同时回答：主循环入口是谁、文件是否被生产源码引用、角色是核心/工具面/兼容/样例/验收/支撑/删除风险中的哪一类。
- 看到 `generic_app_discovery.py` 时要优先检查 `learning_agent/core/agent.py::_computer_discover`；当前事实是主 discover 使用 `windows_app_inventory.query_windows_app_inventory`。

## 2026-06-07 Runtime Trace 经验
- 经验：判断 Computer Use 是否真正接进模型主循环，不能只看工具 schema 是否存在，还要同时看 `model_request_seen`、`tool_call_seen`、`tool_result_seen` 和工具内部 `computer_discover/observe/action` trace。
- 经验：静态源码审计、运行时可达性审计、runtime trace 和真实可见终端验收是四层不同证据；任何一层通过都不能单独代表 `/computer use --full` 完整成熟。
- 经验：瘦身前必须先确认文件角色和引用关系。当前 `generic_app_discovery.py` 已不是主循环 discover 入口，但仍是兼容包装层，应该先迁移旧引用再删除，不能直接删。

## 2026-06-07 真实终端 controller 窗口句柄经验
- 经验：Windows Terminal/cmd 的 `MainWindowHandle` 在启动和承载切换早期可能短暂为空，即使上一轮枚举时看起来非零，也要在调用 `ShowWindowAsync`、`SetForegroundWindow` 前刷新并二次检查。
- 经验：真实可见终端验收失败要先区分“controller 自身窗口控制失败”和“agent 功能断言失败”；本轮第一次失败属于 controller 聚焦竞态，不是 `/computer maturity` 或 runtime trace 断言失败。

## 2026-06-07 Computer Use legacy slimming lesson

- 经验：瘦身不能只看文件名删除；必须先做生产引用扫描、runtime reachability 分类和全量 Computer Use 回归，否则可能把仍被旧命令或验收合同使用的兼容入口删坏。
- 经验：旧 Phase 文件如果继续留在正式源码里，会在长上下文压缩后污染判断，让开发者误以为当前主路径仍是旧 discovery/paint/phase bridge。能迁移成统一 resolver/backend 的，应尽快迁移并删除旧文件。
- 经验：删除旧入口后，测试和真实终端场景里的 marker/token 也要同步改成当前统一语义；否则 maturity 矩阵会继续把项目拉回旧设计词汇。
## 2026-06-07 Computer Use slimming experience: 删除旧路线要删“入口本体”，不只删调用点

- 经验：在 OpenHarness 的 Computer Use 演进中，只把 `run()` 从旧函数调用点改走模型主循环还不够；如果旧函数本体仍留在 `LearningAgent` 或 `computer_use` 正式源码里，后续开发者、测试或上下文压缩后仍可能把它误接回主线。
- 做法：每次瘦身先跑 runtime reachability/source audit，再区分 active runtime core、active tool surface、compatibility wrapper、representative sample、maturity acceptance；确认死入口后，优先删除或迁移入口本体，并让 `/computer maturity` 输出可见 token。
- 门禁：对“已删除旧入口”的结论必须基于源码 AST 或 import/reference 扫描，不要只靠 README、历史记录或口头判断；真实终端场景也要加入同一个 token，防止自动化和终端验收漂移。
- 边界：不是所有带旧 phase 名的文件都能立即删。有些文件仍承担测试工厂、代表样例、兼容命令或 maturity 子报告职责，必须先迁移职责再删除。
## 2026-06-19 Computer Use 资源新鲜度经验：窗口新鲜不等于资源新鲜

- 经验：`fresh_agent_owned_window`、`target_ref_one_to_one=true`、PID/HWND 一对一只能证明 agent 绑定了一个新窗口，不能证明窗口里承载的是新空白资源；Notepad、Word、Excel、浏览器这类资源容器可能在新进程里恢复旧文件或旧标签。
- 做法：Computer Use 的写动作入口不能只依赖 launch/observe 的上一轮状态；如果 action 有绑定窗口且窗口来自 agent-owned launch/target_ref，必须在底层键鼠执行前根据窗口标题、资源文件名、空白标题、用户是否授权已有资源做兜底 `ResourceFreshness` 判断。
- 验收：真实可见终端压力测试要区分三种合法结果：新空白资源完整完成任务；启动前已有旧窗口时零事件要求用户关闭/授权；启动后应用恢复旧资源时零事件要求用户创建空白资源或授权已有资源。不能把后两种安全拒绝误判成“功能失败”，也不能把它们说成“保存成功”。
## 2026-06-19 Computer Use 受控资源启动经验：文档容器不能裸启动
- 经验：Notepad、Word、Excel、浏览器这类“资源容器”即使是 agent 新启动的新窗口，也可能自动恢复旧文件或旧标签；因此窗口新鲜、PID/HWND 一对一、target_ref 一对一都不能单独证明资源新鲜。
- 做法：当用户任务明确要求创建或保存具体本地文件，例如桌面 `1.txt`，启动层应优先使用“应用可执行文件 + 受控资源路径”的 argv/no-shell 启动方式，让目标资源从源头进入应用，而不是依赖模型启动后再 `Ctrl+N` 自救。
- 边界：不能把文件路径参数盲目塞给所有应用；只允许已验证支持该模式的文档类应用，未知应用、单实例应用和聊天类应用仍应走通用 FreshTarget/TargetLease/用户授权流程。
- 验收：以后遇到“受控 driver 可以成功、主循环 open_application 却打开旧文档”的问题，优先比较两者启动参数差异，而不是继续堆提示词或重复修窗口绑定。

## 2026-06-19 Computer Use 经验：模型 reason 会压缩，受控资源必须结构化传递
- 经验：不要假设 `request_access.reason` 或 `open_application.reason` 会完整复述用户原始 prompt；真实模型会把“保存为桌面 1.txt”压缩成“保存到桌面”，导致文件名丢失。
- 做法：需要跨多步工具调用使用的信息，应该在分类/规划阶段提取成脱敏结构化字段，例如 `controlled_resource_name=1.txt`、`controlled_resource_location_hint=desktop`，再通过 session state 传递。
- 经验：`/computer use --full` 可能先创建并缓存 v2 context，真实任务 prompt 后到；因此只在 host 构造时同步上下文不够，复用 host 的每次工具调用前也要刷新当前 agent 上下文。
- 验收：以后排查“driver 成功但主循环打开旧文档”时，必须检查真实工具 payload 是否包含受控资源字段和 argv 启动参数，不能只看 PID/HWND/target_ref 是否为新窗口。

## 2026-06-19 Computer Use 验收经验：普通压力测试默认不要关闭自动同意
- 经验：`start_oauth_agent.ps1` 已默认开启 `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS=1`，但 acceptance scenario 里的 `environment` 会覆盖启动脚本默认值；如果普通压力测试场景写成 `0`，controller 就会反复代输 `Y`。
- 做法：普通 Computer Use 功能/压力测试场景应保持 `LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS=1` 或不显式关闭；只有 `permission_ui`、`permission_denial` 这类专门验收权限弹窗和拒绝路径的场景才允许设置为 `0`。
- 验收：需要同时看 `permission_sent_count=0`、事件流包含 `permission_auto_approved`、不包含 `permission_required`，不能只看场景最终成功标记。

## 2026-06-19 Computer Use 经验：脱敏事件不等于真实可输入文本
- 经验：Stage batch 里的 `text_sha256_16` 和 `text_length` 只能做审计，不能被真实 Unicode sender 当作待输入文本；否则真实 GUI 会出现“动作链路看似执行，窗口里没有输入”的假进展。
- 做法：通用 Computer Use 文本输入要分三层处理：公开工具结果只保留脱敏摘要；dispatcher 只在最后一跳声明 `requires_raw_text=true` 时开启短通道；受控物理 sender 只接受私有 `_secure_plaintext_text`，并在调用真实后端前临时恢复 `text`。
- 验收：以后排查文本输入失败，必须同时看 `requested_text` 是否正确、`secure_plaintext_text_channel_missing` 是否出现、公开结果是否泄露原文、真实后端是否报告 `low_level_event_count>0`；不能只看哈希或事件数量。
## 2026-06-19 Computer Use 经验：高层桌面任务未完成必须变成运行时 pending
- 经验：`desktop_task_incomplete` pending 允许 `observe` 只是为了获得阶段边界事实，不代表可以把 pending 降级成普通 `desktop_observe_before_action`；observe/screenshot 的普通动作 marker 不应覆盖高层未完成状态。
- 经验：`desktop_task_incomplete=true` 不能只作为 final gate 的文本判断信号；它必须进入 `actionability_pending`，否则模型仍可能在下一轮退回 `key/click/drag` 等原子动作，把通用 Stage Runtime 拆散。
- 做法：高层 `desktop_task` 工具未完成时输出稳定 marker，例如 `OPENHARNESS_DESKTOP_TASK_INCOMPLETE`，并声明 `next_required_tool=mcp__computer-use__desktop_task`、`next_allowed_tools=mcp__computer-use__desktop_task,mcp__computer-use__observe,mcp__computer-use__request_access`。
- 门禁：在该 marker 激活期间，除高层任务、阶段观察和必要授权外，所有桌面原子动作都应被阻断；这不是 Notepad/Paint 专项，而是所有通用 GUI 任务的收敛边界。
- 经验：文本正文抽取要识别用户常见标签词，例如“输入文本 `hello everyone`”和“准确文本：hello everyone”；标签词是说明，不是正文。否则 Stage Runtime 会正确执行错误内容，形成假进度。
- 验收：以后遇到复杂 GUI 任务超时或提前 final，必须同时检查 `desktop_task_completed/desktop_task_incomplete`、`stage_count/completed_stage_count`、`actionability_pending`、后续工具是否被限制在 `desktop_task/observe`，不能只看 low-level event 数量。
