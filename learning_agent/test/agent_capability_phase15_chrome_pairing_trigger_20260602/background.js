// 新增代码+ChromeExtensionStage5: 固定 native host 名称；若没有这行代码，扩展无法知道连接哪个本地 host。
const HOST_NAME = "com.openharness.learning_agent";

// 新增代码+ChromeExtensionStage5: 保存当前 native messaging 端口；若没有这行代码，状态请求无法复用连接。
let nativePort = null;

// 新增代码+ChromeExtensionStage6: 保存命令轮询定时器；若没有这行代码，扩展无法持续拉取 provider 下发的写动作。
let commandPollTimer = null;

// 新增代码+ChromeExtensionStage5: 连接本地 host 的小函数；若没有这行代码，每个只读请求都要重复连接逻辑。
function connectHost() {
  // 新增代码+ChromeExtensionStage5: 已连接时直接返回旧端口；若没有这行代码，重复连接会制造多个 host 进程。
  if (nativePort) {
    // 新增代码+ChromeExtensionStage5: 返回可复用端口；若没有这行代码，调用方拿不到连接对象。
    return nativePort;
  }
  // 新增代码+ChromeExtensionStage5: 通过 Chrome native messaging 连接 host；若没有这行代码，扩展无法把只读结果交给 learning_agent。
  nativePort = chrome.runtime.connectNative(HOST_NAME);
  // 新增代码+Phase2Pairing: 连接后发送配对摘要；如果没有这行代码，host 无法记录 extension/device/session 身份。
  nativePort.postMessage(buildPairingPayload());
  // 新增代码+ChromeExtensionStage6: 监听 native host 返回的消息；若没有这行代码，poll_commands 响应不会被处理。
  nativePort.onMessage.addListener((message) => {
    // 新增代码+ChromeExtensionStage6: 交给统一处理函数；若没有这行代码，连接层会混入命令执行逻辑。
    handleHostMessage(message);
  });
  // 新增代码+ChromeExtensionStage5: 监听断开并清空端口；若没有这行代码，断线后状态会误报仍连接。
  nativePort.onDisconnect.addListener(() => {
    // 新增代码+ChromeExtensionStage5: 清空断开的端口引用；若没有这行代码，下一次请求会复用坏连接。
    nativePort = null;
    // 新增代码+ChromeExtensionStage6: 断开后清理轮询定时器；若没有这行代码，后台会继续向坏端口发消息。
    if (commandPollTimer) {
      // 新增代码+ChromeExtensionStage6: 停止旧轮询；若没有这行代码，重连后可能出现多个轮询。
      clearInterval(commandPollTimer);
      // 新增代码+ChromeExtensionStage6: 清空定时器引用；若没有这行代码，后续无法重新启动轮询。
      commandPollTimer = null;
    }
  });
  // 新增代码+ChromeExtensionStage5: 返回新连接端口；若没有这行代码，请求无法发送。
  return nativePort;
}

// 新增代码+ChromeExtensionStage6: 向 native host 安全发送消息；若没有这行代码，各处会重复 connectHost/postMessage。
function postToHost(payload) {
  // 新增代码+ChromeExtensionStage6: 获取或创建 native port；若没有这行代码，消息没有通道。
  const port = connectHost();
  // 新增代码+ChromeExtensionStage6: 把 payload 发给 native host；若没有这行代码，host 收不到轮询或结果。
  port.postMessage(payload);
}

// 修改代码+Phase15ChromePairingTrigger: 构造当前扩展配对摘要，并可携带 host 下发的 pairing request；如果没有这段函数，native host 不知道 device/session/extension 身份，也无法闭合终端触发请求。
function buildPairingPayload(pairingRequest = {}) {
  // 新增代码+Phase2Pairing: 从 Chrome runtime 读取扩展 id；如果没有这行代码，host 无法记录 extension_id。
  const extensionId = chrome.runtime.id || "";
  // 新增代码+Phase2Pairing: 使用扩展 id 构造本机 device id 的稳定摘要；如果没有这行代码，每次连接都难以关联同一扩展。
  const deviceId = `chrome-extension-${extensionId}`;
  // 新增代码+Phase2Pairing: 使用时间构造轻量 session id；如果没有这行代码，状态无法区分不同浏览器会话。
  const sessionId = `chrome-session-${Date.now()}`;
  // 新增代码+Phase15ChromePairingTrigger: 读取 host 下发的 request id；如果没有这行代码，bridge 无法把本次配对和终端触发请求对应起来。
  const requestId = pairingRequest && pairingRequest.request_id ? String(pairingRequest.request_id) : "";
  // 新增代码+Phase15ChromePairingTrigger: 读取 host 下发的 request nonce；如果没有这行代码，配对请求缺少防混淆审计字段。
  const requestNonce = pairingRequest && pairingRequest.request_nonce ? String(pairingRequest.request_nonce) : "";
  // 修改代码+Phase15ChromePairingTrigger: 返回不含 cookie/token/password 的配对对象，并带回 request_id/request_nonce；如果没有这行代码，配对消息可能缺必需字段或无法关闭 pending 请求。
  return { action: "pair_device", extension_id: extensionId, device_id: deviceId, session_id: sessionId, allowed_origins: [], request_id: requestId, request_nonce: requestNonce };
}

// 新增代码+Phase2Pairing: 把当前页面用户 prompt 发给 native host；如果没有这段函数，Chrome 侧无法主动发起 agent 任务。
async function pushBrowserPrompt(promptText) {
  // 新增代码+Phase2Pairing: 查询当前活动标签页；如果没有这行代码，prompt 缺少 URL/title 上下文。
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  // 新增代码+Phase2Pairing: 取活动标签页或空对象；如果没有这行代码，空窗口会导致属性访问错误。
  const tab = tabs[0] || {};
  // 新增代码+Phase2Pairing: 发送 browser_prompt 消息给 host；如果没有这行代码，prompt 不会进入 durable queue。
  postToHost({ action: "browser_prompt", prompt: String(promptText || ""), url: tab.url || "", title: tab.title || "", tab_id: tab.id ? `chrome-tab-${tab.id}` : "" });
}

// 新增代码+ChromeExtensionStage6: 启动命令轮询；若没有这行代码，provider 入队后的命令无法被扩展发现。
function ensureCommandPolling() {
  // 新增代码+ChromeExtensionStage6: 已经轮询时直接返回；若没有这行代码，会创建多个定时器重复执行命令。
  if (commandPollTimer) {
    // 新增代码+ChromeExtensionStage6: 返回避免重复注册；若没有这行代码，轮询会越开越多。
    return;
  }
  // 新增代码+ChromeExtensionStage6: 每秒拉取一次待执行命令；若没有这行代码，写动作不会自动推进。
  commandPollTimer = setInterval(() => {
    // 新增代码+ChromeExtensionStage6: 发送 poll_commands 请求；若没有这行代码，host 不会返回 pending 命令。
    postToHost({ action: "poll_commands" });
  }, 1000);
  // 新增代码+ChromeExtensionStage6: 启动后立刻拉取一次；若没有这行代码，第一次命令最多要等一个轮询周期。
  postToHost({ action: "poll_commands" });
}

// 新增代码+ChromeExtensionStage5: 收集 Chrome 标签页摘要；若没有这行代码，tabs_context 没有数据来源。
async function collectTabsContext() {
  // 新增代码+ChromeExtensionStage5: 查询当前窗口和其他窗口的标签页；若没有这行代码，扩展无法知道 active tab。
  const tabs = await chrome.tabs.query({});
  // 新增代码+ChromeExtensionStage5: 只保留 id、url、title、active、windowId 这些只读摘要；若没有这行代码，host 响应可能混入过多浏览器字段。
  return tabs.map((tab) => ({
    // 新增代码+ChromeExtensionStage5: 保存 Chrome tab id；若没有这行代码，host 无法生成稳定 tab_id。
    id: tab.id,
    // 新增代码+ChromeExtensionStage5: 保存页面 URL 摘要；若没有这行代码，用户无法判断当前页位置。
    url: tab.url || "",
    // 新增代码+ChromeExtensionStage5: 保存页面标题摘要；若没有这行代码，标签页列表不易读。
    title: tab.title || "",
    // 新增代码+ChromeExtensionStage5: 保存 active 标记；若没有这行代码，默认操作目标不清楚。
    active: Boolean(tab.active),
    // 新增代码+ChromeExtensionStage5: 保存窗口 id；若没有这行代码，多窗口排查会缺少线索。
    windowId: tab.windowId
  }));
}

// 新增代码+ChromeExtensionStage5: 读取当前活动页的可见文本摘要；若没有这行代码，插件只读 MVP 不能提供页面内容。
async function readActivePage() {
  // 新增代码+ChromeExtensionStage5: 查找当前窗口活动标签页；若没有这行代码，无法决定读取哪个页面。
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  // 新增代码+ChromeExtensionStage5: 取第一个活动标签页；若没有这行代码，空数组会导致后续访问错误。
  const tab = tabs[0];
  // 新增代码+ChromeExtensionStage5: 没有活动页时返回空摘要；若没有这行代码，状态请求会抛异常。
  if (!tab || !tab.id) {
    // 新增代码+ChromeExtensionStage5: 返回机器可读空页面结果；若没有这行代码，host 无法区分无页面和失败。
    return { tab: null, page: { visibleText: "", elements: [] } };
  }
  // 新增代码+ChromeExtensionStage5: 请求 content script 收集可见页面内容；若没有这行代码，background 无法直接读取 DOM。
  const page = await chrome.tabs.sendMessage(tab.id, { action: "collect_visible_page" });
  // 新增代码+ChromeExtensionStage5: 返回 tab 摘要和页面摘要；若没有这行代码，host 不能生成 browser_snapshot。
  return {
    // 新增代码+ChromeExtensionStage5: 返回活动 tab 的最小摘要；若没有这行代码，页面内容缺少来源。
    tab: { id: tab.id, url: tab.url || "", title: tab.title || "", active: true, windowId: tab.windowId },
    // 新增代码+ChromeExtensionStage5: 返回 content script 的页面结果；若没有这行代码，调用方拿不到可见文本。
    page: page || { visibleText: "", elements: [] }
  };
}

// 新增代码+ChromeExtensionStage6: 从 command 里解析目标 Chrome tab id；若没有这行代码，写动作不知道发给哪个标签页。
async function tabIdForCommand(command) {
  // 新增代码+ChromeExtensionStage6: 读取命令 target；若没有这行代码，空命令会触发属性错误。
  const target = command.target || {};
  // 新增代码+ChromeExtensionStage6: page_id 使用 chrome-tab-数字 格式时直接映射；若没有这行代码，provider 的 tab context 不能定位真实 tab。
  if (target.page_id && String(target.page_id).startsWith("chrome-tab-")) {
    // 新增代码+ChromeExtensionStage6: 提取 Chrome tab 数字 id；若没有这行代码，tabs.sendMessage 不能使用字符串 page_id。
    return Number(String(target.page_id).replace("chrome-tab-", ""));
  }
  // 新增代码+ChromeExtensionStage6: 默认使用当前窗口活动标签页；若没有这行代码，省略 page_id 的动作没有目标。
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  // 新增代码+ChromeExtensionStage6: 返回活动 tab id 或 0；若没有这行代码，空窗口会导致访问 undefined。
  return tabs[0] && tabs[0].id ? tabs[0].id : 0;
}

// 新增代码+ChromeExtensionStage6: 执行 host 下发的单条浏览器命令；若没有这行代码，命令轮询只能拿到数据不能操作页面。
async function executeBrowserCommand(command) {
  // 新增代码+ChromeExtensionStage6: navigate 动作由 background 直接更新标签页；若没有这行代码，打开页面无法执行。
  if (command.action === "navigate") {
    // 新增代码+ChromeExtensionStage6: 找到目标 tab；若没有这行代码，导航不知道更新哪个标签页。
    const tabId = await tabIdForCommand(command);
    // 新增代码+ChromeExtensionStage6: 读取目标 URL；若没有这行代码，导航没有地址。
    const url = String((command.target || {}).url || "");
    // 新增代码+ChromeExtensionStage6: URL 为空时抛错；若没有这行代码，Chrome 会收到无效导航请求。
    if (!url) {
      // 新增代码+ChromeExtensionStage6: 抛出清楚错误；若没有这行代码，调用方只会看到模糊失败。
      throw new Error("navigate 缺少 url");
    }
    // 新增代码+ChromeExtensionStage6: 更新目标标签页 URL；若没有这行代码，browser_open 不会影响真实 Chrome。
    const tab = await chrome.tabs.update(tabId, { url });
    // 新增代码+ChromeExtensionStage6: 返回导航结果摘要；若没有这行代码，provider 无法确认打开结果。
    return { summary: "navigate 完成", tab: { id: tab.id, url: tab.url || url, title: tab.title || "", active: true, windowId: tab.windowId }, visibleText: "" };
  }
  // 新增代码+ChromeExtensionStage6: 其他动作需要发给 content script；若没有这行代码，页面 DOM 无法被操作。
  const tabId = await tabIdForCommand(command);
  // 新增代码+ChromeExtensionStage6: 没有 tab id 时抛错；若没有这行代码，sendMessage 会失败得不清楚。
  if (!tabId) {
    // 新增代码+ChromeExtensionStage6: 抛出可读错误；若没有这行代码，用户不知道没有活动标签页。
    throw new Error("没有可用的 Chrome 标签页");
  }
  // 新增代码+ChromeExtensionStage6: 请求 content script 执行动作；若没有这行代码，click/type/key/locate 不会进入页面上下文。
  const response = await chrome.tabs.sendMessage(tabId, { action: "perform_browser_action", command });
  // 新增代码+ChromeExtensionStage6: content script 报错时抛出；若没有这行代码，失败动作可能被误报成功。
  if (!response || !response.ok) {
    // 新增代码+ChromeExtensionStage6: 抛出 content script 的错误文本；若没有这行代码，provider 看不到真实失败原因。
    throw new Error(response && response.error ? response.error : "content script action failed");
  }
  // 新增代码+ChromeExtensionStage6: 读取 tab 摘要补到结果里；若没有这行代码，provider 结果缺 URL 和标题。
  const tab = await chrome.tabs.get(tabId);
  // 新增代码+ChromeExtensionStage6: 返回动作结果和 tab 摘要；若没有这行代码，host 无法保存完整证据。
  return { ...(response.result || {}), tab: { id: tab.id, url: tab.url || "", title: tab.title || "", active: tab.active, windowId: tab.windowId } };
}

// 新增代码+ChromeExtensionStage6: 执行并回传一条命令；若没有这行代码，轮询到命令后无法把结果送回 host。
async function runCommandAndReport(command) {
  // 新增代码+ChromeExtensionStage6: 用 try/catch 保证成功失败都会回传；若没有这行代码，失败动作会让 provider 等到超时。
  try {
    // 新增代码+ChromeExtensionStage6: 执行真实页面动作；若没有这行代码，命令不会产生页面变化。
    const result = await executeBrowserCommand(command);
    // 新增代码+ChromeExtensionStage6: 把成功结果发回 native host；若没有这行代码，provider 无法完成工具调用。
    postToHost({ action: "action_result", command_id: command.command_id, tool_name: command.tool_name, ok: true, result });
  } catch (error) {
    // 新增代码+ChromeExtensionStage6: 把失败结果发回 native host；若没有这行代码，失败会变成等待超时。
    postToHost({ action: "action_result", command_id: command.command_id, tool_name: command.tool_name, ok: false, error: String(error && error.message ? error.message : error) });
  }
}

// 新增代码+ChromeExtensionStage6: 处理 native host 返回的消息；若没有这行代码，poll_commands 响应不会触发执行。
function handleHostMessage(message) {
  // 新增代码+ChromeExtensionStage6: 只处理 poll_commands 响应；若没有这行代码，普通响应可能被误当命令。
  if (!message || message.action !== "poll_commands") {
    // 新增代码+ChromeExtensionStage6: 非命令响应直接忽略；若没有这行代码，状态响应会干扰执行循环。
    return;
  }
  // 新增代码+Phase15ChromePairingTrigger: 读取 native host 下发的配对请求；如果没有这行代码，终端 pairing-start-confirm 写入后真实扩展不会响应。
  const pairingRequest = message && message.pairing_request && typeof message.pairing_request === "object" ? message.pairing_request : {};
  // 新增代码+Phase15ChromePairingTrigger: 有待处理配对请求时立即回传 pair_device；如果没有这行代码，pending_pairing_request 会一直停留在 pending。
  if (pairingRequest.request_id) {
    // 新增代码+Phase15ChromePairingTrigger: 把 request_id/request_nonce 带回 native host；如果没有这行代码，bridge 无法把请求标记 completed。
    postToHost(buildPairingPayload(pairingRequest));
  }
  // 新增代码+ChromeExtensionStage6: 读取命令列表；若没有这行代码，空响应会导致遍历异常。
  const commands = Array.isArray(message.commands) ? message.commands : [];
  // 新增代码+ChromeExtensionStage6: 逐条执行命令；若没有这行代码，pending 队列不会被消费。
  commands.forEach((command) => {
    // 新增代码+ChromeExtensionStage6: 触发异步执行并回传结果；若没有这行代码，命令只会留在内存里。
    runCommandAndReport(command);
  });
}

// 新增代码+ChromeExtensionStage5: 处理扩展内部只读请求；若没有这行代码，options 页面和调试入口无法读取状态。
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // 新增代码+ChromeExtensionStage5: 明确本阶段不使用 sender；若没有这行代码，读者会以为来源参与权限判断。
  void sender;
  // 新增代码+ChromeExtensionStage5: 异步执行只读动作；若没有这行代码，Promise 结果无法发送给调用方。
  (async () => {
    // 新增代码+ChromeExtensionStage5: 连接 native host；若没有这行代码，只读结果不会进入本地 agent。
    const port = connectHost();
    // 新增代码+ChromeExtensionStage6: 确保命令轮询已启动；若没有这行代码，用户只读检查后写动作仍不会自动执行。
    ensureCommandPolling();
    // 新增代码+ChromeExtensionStage5: 根据 action 分发只读请求；若没有这行代码，所有请求都会走同一分支。
    if (message && message.action === "tabs_context") {
      // 新增代码+ChromeExtensionStage5: 收集标签页上下文；若没有这行代码，tabs_context 请求没有结果。
      const tabs = await collectTabsContext();
      // 新增代码+ChromeExtensionStage5: 把只读结果发给 host；若没有这行代码，learning_agent 无法看到当前标签页。
      port.postMessage({ action: "tabs_context", tabs });
      // 新增代码+ChromeExtensionStage5: 返回给扩展调用方；若没有这行代码，options 页面不会显示结果。
      sendResponse({ ok: true, tabs });
      // 新增代码+ChromeExtensionStage5: 结束 tabs_context 分支；若没有这行代码，后续分支可能继续执行。
      return;
    }
    // 新增代码+ChromeExtensionStage5: 处理页面只读请求；若没有这行代码，read_page 请求无法工作。
    if (message && message.action === "read_page") {
      // 新增代码+ChromeExtensionStage5: 读取活动页可见内容；若没有这行代码，页面摘要没有来源。
      const snapshot = await readActivePage();
      // 新增代码+ChromeExtensionStage5: 把页面摘要发给 host；若没有这行代码，provider 无法返回 browser_snapshot。
      port.postMessage({ action: "read_page", ...snapshot });
      // 新增代码+ChromeExtensionStage5: 返回给扩展调用方；若没有这行代码，调试页面拿不到结果。
      sendResponse({ ok: true, snapshot });
      // 新增代码+ChromeExtensionStage5: 结束 read_page 分支；若没有这行代码，未知分支可能覆盖响应。
      return;
    }
    // 新增代码+Phase2Pairing: 处理浏览器侧主动发起 prompt；如果没有这行代码，页面/插件 UI 不能把任务交给 agent。
    if (message && message.action === "browser_prompt") {
      // 新增代码+Phase2Pairing: 把 prompt 推给 native host；如果没有这行代码，用户在 Chrome 里的任务不会进入 durable queue。
      await pushBrowserPrompt(message.prompt || "");
      // 新增代码+Phase2Pairing: 返回推送成功；如果没有这行代码，调用方不知道请求已提交。
      sendResponse({ ok: true });
      // 新增代码+Phase2Pairing: 结束 browser_prompt 分支；如果没有这行代码，后续未知动作会覆盖响应。
      return;
    }
    // 新增代码+ChromeExtensionStage5: 未知动作返回只读错误；若没有这行代码，调用方不知道请求被忽略。
    sendResponse({ ok: false, error: "read-only action is not supported" });
  })();
  // 新增代码+ChromeExtensionStage5: 告诉 Chrome 本监听器会异步响应；若没有这行代码，sendResponse 可能失效。
  return true;
});

// 新增代码+ChromeExtensionStage6: 扩展后台启动时就连接并轮询命令；若没有这行代码，用户无需打开 options 时写动作不会执行。
ensureCommandPolling();
