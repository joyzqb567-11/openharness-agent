// 新增代码+ChromeExtensionStage5: 收集页面可见文本摘要；若没有这行代码，插件无法提供 read_page 只读能力。
function collectVisibleText() {
  // 新增代码+ChromeExtensionStage5: 读取 body 可见文本并兜底空字符串；若没有这行代码，无 body 页面会抛错。
  const rawText = document.body ? (document.body.innerText || "") : "";
  // 新增代码+ChromeExtensionStage5: 归一化空白并限制长度；若没有这行代码，大页面会把 host 消息撑得过大。
  return rawText.replace(/\s+/g, " ").trim().slice(0, 8000);
}

// 新增代码+ChromeExtensionStage5: 收集可交互元素的只读摘要；若没有这行代码，页面快照缺少可定位线索。
function collectElementSummaries() {
  // 新增代码+ChromeExtensionStage5: 选择常见可交互元素；若没有这行代码，按钮和输入框不会进入摘要。
  const nodes = Array.from(document.querySelectorAll("a,button,input,textarea,select,[role='button'],[role='link']")).slice(0, 80);
  // 新增代码+ChromeExtensionStage5: 转成安全摘要对象；若没有这行代码，DOM 节点无法通过消息协议发送。
  return nodes.map((node, index) => {
    // 新增代码+ChromeExtensionStage5: 读取元素矩形；若没有这行代码，模型无法知道元素大概位置。
    const rect = node.getBoundingClientRect();
    // 新增代码+ChromeExtensionStage5: 读取人类可见标签；若没有这行代码，元素摘要不易识别。
    const label = (node.innerText || node.value || node.getAttribute("aria-label") || node.getAttribute("title") || node.getAttribute("placeholder") || "").replace(/\s+/g, " ").trim();
    // 新增代码+ChromeExtensionStage5: 返回最小元素摘要；若没有这行代码，read_page 缺少结构化元素。
    return {
      // 新增代码+ChromeExtensionStage5: 保存本次摘要里的元素序号；若没有这行代码，元素列表不可引用。
      id: index + 1,
      // 新增代码+ChromeExtensionStage5: 保存标签名；若没有这行代码，调用方不知道元素类型。
      tag: node.tagName.toLowerCase(),
      // 新增代码+ChromeExtensionStage5: 保存可见标签并限制长度；若没有这行代码，长文本会污染摘要。
      label: label.slice(0, 200),
      // 新增代码+ChromeExtensionStage5: 保存元素可见性；若没有这行代码，隐藏元素会误导模型。
      visible: Boolean(rect.width && rect.height),
      // 新增代码+ChromeExtensionStage5: 保存横坐标；若没有这行代码，后续视觉证据缺位置。
      x: Math.round(rect.x),
      // 新增代码+ChromeExtensionStage5: 保存纵坐标；若没有这行代码，后续视觉证据缺位置。
      y: Math.round(rect.y),
      // 新增代码+ChromeExtensionStage5: 保存宽度；若没有这行代码，元素范围不清楚。
      width: Math.round(rect.width),
      // 新增代码+ChromeExtensionStage5: 保存高度；若没有这行代码，元素范围不清楚。
      height: Math.round(rect.height)
    };
  });
}

// 新增代码+ChromeExtensionStage6: 复用可交互元素集合；若没有这行代码，点击、输入和视觉定位会各自查询 DOM。
function interactiveNodes() {
  // 新增代码+ChromeExtensionStage6: 选择常见可交互元素并限制数量；若没有这行代码，大页面会让动作定位过慢。
  return Array.from(document.querySelectorAll("a,button,input,textarea,select,[role='button'],[role='link']")).slice(0, 200);
}

// 新增代码+ChromeExtensionStage6: 把任意文本归一化；若没有这行代码，按可见文本定位会受换行和多空格影响。
function normalizeText(value) {
  // 新增代码+ChromeExtensionStage6: 转字符串、合并空白并去掉首尾空格；若没有这行代码，标签匹配不稳定。
  return String(value || "").replace(/\s+/g, " ").trim();
}

// 新增代码+ChromeExtensionStage6: 读取元素的人类可见标签；若没有这行代码，按 label/text 定位无法复用同一规则。
function nodeLabel(node) {
  // 新增代码+ChromeExtensionStage6: 按常见可见属性组合标签；若没有这行代码，输入框 placeholder 或按钮文本会漏匹配。
  return normalizeText(node.innerText || node.value || node.getAttribute("aria-label") || node.getAttribute("title") || node.getAttribute("placeholder") || "");
}

// 新增代码+ChromeExtensionStage6: 根据 provider 命令定位页面元素；若没有这行代码，click/type 无法找到目标。
function resolveTarget(command) {
  // 新增代码+ChromeExtensionStage6: 读取命令里的安全目标对象；若没有这行代码，空命令会导致属性访问异常。
  const target = command.target || {};
  // 新增代码+ChromeExtensionStage6: 坐标优先，因为视觉定位可能已经给出中心点；若没有这行代码，坐标点击会被迫走 selector。
  if (target.x !== undefined && target.y !== undefined && String(target.x) !== "" && String(target.y) !== "") {
    // 新增代码+ChromeExtensionStage6: 通过视口坐标获取元素；若没有这行代码，坐标点击没有目标节点。
    return document.elementFromPoint(Number(target.x), Number(target.y));
  }
  // 新增代码+ChromeExtensionStage6: selector 是最直接的定位方式；若没有这行代码，CSS 精确定位不可用。
  if (target.selector) {
    // 新增代码+ChromeExtensionStage6: 返回 CSS 选择器匹配的第一个元素；若没有这行代码，指定 selector 不会生效。
    return document.querySelector(String(target.selector));
  }
  // 新增代码+ChromeExtensionStage6: element_id 可引用页面快照中的序号；若没有这行代码，snapshot 元素无法被后续动作复用。
  if (target.element_id) {
    // 新增代码+ChromeExtensionStage6: 把 element_id 转成从 1 开始的序号；若没有这行代码，元素引用无法映射回 DOM 节点。
    const index = Number(String(target.element_id).replace(/^element-/, "")) - 1;
    // 新增代码+ChromeExtensionStage6: 从可交互元素列表里取对应节点；若没有这行代码，element_id 分支没有结果。
    return interactiveNodes()[index] || null;
  }
  // 新增代码+ChromeExtensionStage6: label 或 text 可用于模糊定位；若没有这行代码，复杂页面只能依赖 selector。
  const wanted = normalizeText(target.label || target.text);
  // 新增代码+ChromeExtensionStage6: 没有定位文本时返回当前焦点；若没有这行代码，无目标输入不能作用于已聚焦元素。
  if (!wanted) {
    // 新增代码+ChromeExtensionStage6: 返回当前活动元素；若没有这行代码，焦点输入和按键没有目标。
    return document.activeElement;
  }
  // 新增代码+ChromeExtensionStage6: 遍历可交互元素找匹配文本；若没有这行代码，文本定位没有候选。
  return interactiveNodes().find((node) => {
    // 新增代码+ChromeExtensionStage6: 读取候选标签；若没有这行代码，无法比较文本。
    const label = nodeLabel(node);
    // 新增代码+ChromeExtensionStage6: exact=true 时要求完全一致；若没有这行代码，精确点击可能误点相似按钮。
    if (target.exact === true) {
      // 新增代码+ChromeExtensionStage6: 返回精确匹配结果；若没有这行代码，exact 参数不会生效。
      return label === wanted;
    }
    // 新增代码+ChromeExtensionStage6: 默认模糊包含匹配；若没有这行代码，长按钮文本不易匹配。
    return label.includes(wanted);
  }) || null;
}

// 新增代码+ChromeExtensionStage6: 构造动作后的页面摘要；若没有这行代码，provider 无法拿到 observation 证据。
function actionObservation(summary) {
  // 新增代码+ChromeExtensionStage6: 返回短摘要、可见文本和元素候选；若没有这行代码，写动作完成后没有页面反馈。
  return { summary, visibleText: collectVisibleText(), elements: collectElementSummaries() };
}

// 新增代码+ChromeExtensionStage6: 在 DOM 中执行插件命令；若没有这行代码，background 只能收到命令却不能操作页面。
async function performBrowserAction(command) {
  // 新增代码+ChromeExtensionStage6: 读取动作名和目标；若没有这行代码，分发逻辑没有输入。
  const action = command.action;
  // 新增代码+ChromeExtensionStage6: 定位目标元素；若没有这行代码，click/type/locate 无法确定对象。
  const targetNode = resolveTarget(command);
  // 新增代码+ChromeExtensionStage6: visual_locate 只返回候选，不改变页面；若没有这行代码，插件缺视觉定位辅助。
  if (action === "visual_locate") {
    // 新增代码+ChromeExtensionStage6: 返回候选元素摘要；若没有这行代码，调用方看不到坐标。
    return actionObservation("visual_locate 完成");
  }
  // 新增代码+ChromeExtensionStage6: wait 动作按毫秒等待；若没有这行代码，多步骤流程无法稳定等待。
  if (action === "wait") {
    // 新增代码+ChromeExtensionStage6: 读取等待毫秒数并设置默认值；若没有这行代码，wait 命令没有时长。
    const milliseconds = Number((command.target || {}).milliseconds || 300);
    // 新增代码+ChromeExtensionStage6: 用 Promise 延迟；若没有这行代码，wait 会立即返回。
    await new Promise((resolve) => setTimeout(resolve, Math.max(0, Math.min(milliseconds, 30000))));
    // 新增代码+ChromeExtensionStage6: 返回等待后的页面摘要；若没有这行代码，wait 动作缺结果。
    return actionObservation("wait 完成");
  }
  // 新增代码+ChromeExtensionStage6: 非 wait/locate 动作必须有目标或焦点；若没有这行代码，空目标会导致后续异常不清楚。
  if (!targetNode) {
    // 新增代码+ChromeExtensionStage6: 抛出可读错误；若没有这行代码，调用方只会看到 null 属性错误。
    throw new Error("未找到可操作元素");
  }
  // 新增代码+ChromeExtensionStage6: click 动作模拟用户点击；若没有这行代码，插件无法点击按钮或链接。
  if (action === "click") {
    // 新增代码+ChromeExtensionStage6: 聚焦目标元素；若没有这行代码，部分控件点击前不会获得焦点。
    targetNode.focus && targetNode.focus();
    // 新增代码+ChromeExtensionStage6: 调用 DOM click；若没有这行代码，页面状态不会改变。
    targetNode.click();
    // 新增代码+ChromeExtensionStage6: 返回点击结果摘要；若没有这行代码，provider 无法确认点击完成。
    return actionObservation("click 完成");
  }
  // 新增代码+ChromeExtensionStage6: type 动作向输入控件写入文本；若没有这行代码，插件无法填写表单。
  if (action === "type") {
    // 新增代码+ChromeExtensionStage6: 读取要输入的文本；若没有这行代码，输入内容没有来源。
    const text = String((command.target || {}).input_text !== undefined ? (command.target || {}).input_text : ((command.target || {}).text || "")); // 修改代码+ChromeExtensionStage6: 优先读取 input_text 作为输入内容；若没有这行代码，纯文本输入会被误当定位文本。
    // 新增代码+ChromeExtensionStage6: 聚焦目标输入框；若没有这行代码，输入事件可能不触发。
    targetNode.focus && targetNode.focus();
    // 新增代码+ChromeExtensionStage6: clear=true 默认覆盖旧内容；若没有这行代码，测试和用户预期可能变成追加。
    if ((command.target || {}).clear !== false && "value" in targetNode) {
      // 新增代码+ChromeExtensionStage6: 清空旧值；若没有这行代码，输入会和旧内容混在一起。
      targetNode.value = "";
    }
    // 新增代码+ChromeExtensionStage6: 对支持 value 的控件写入文本；若没有这行代码，输入框不会变化。
    if ("value" in targetNode) {
      // 新增代码+ChromeExtensionStage6: 写入或追加文本；若没有这行代码，用户文本不会进入控件。
      targetNode.value = String(targetNode.value || "") + text;
    }
    // 新增代码+ChromeExtensionStage6: 派发 input 事件通知前端框架；若没有这行代码，React/Vue 可能不知道值变化。
    targetNode.dispatchEvent(new Event("input", { bubbles: true }));
    // 新增代码+ChromeExtensionStage6: 派发 change 事件通知表单；若没有这行代码，部分页面不会保存输入值。
    targetNode.dispatchEvent(new Event("change", { bubbles: true }));
    // 新增代码+ChromeExtensionStage6: 返回字符数摘要；若没有这行代码，输入结果无法审计。
    return actionObservation(`type 完成，字符数=${text.length}`);
  }
  // 新增代码+ChromeExtensionStage6: press_key 动作向当前焦点派发键盘事件；若没有这行代码，Enter/Escape 无法表达。
  if (action === "press_key") {
    // 新增代码+ChromeExtensionStage6: 读取按键名；若没有这行代码，按键事件没有 key。
    const key = String((command.target || {}).key || "Enter");
    // 新增代码+ChromeExtensionStage6: 聚焦目标；若没有这行代码，按键可能发给错误元素。
    targetNode.focus && targetNode.focus();
    // 新增代码+ChromeExtensionStage6: 派发 keydown；若没有这行代码，页面快捷键监听收不到按下事件。
    targetNode.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true }));
    // 新增代码+ChromeExtensionStage6: Enter 时尝试触发表单提交；若没有这行代码，常见搜索框回车不会提交。
    if (key === "Enter" && targetNode.form && targetNode.form.requestSubmit) {
      // 新增代码+ChromeExtensionStage6: 请求表单提交；若没有这行代码，Enter 可能只触发键盘事件不提交。
      targetNode.form.requestSubmit();
    }
    // 新增代码+ChromeExtensionStage6: 派发 keyup；若没有这行代码，页面可能认为按键一直按下。
    targetNode.dispatchEvent(new KeyboardEvent("keyup", { key, bubbles: true }));
    // 新增代码+ChromeExtensionStage6: 返回按键结果摘要；若没有这行代码，调用方不知道按了哪个键。
    return actionObservation(`press_key 完成，key=${key}`);
  }
  // 新增代码+ChromeExtensionStage6: scroll 动作滚动到目标元素；若没有这行代码，长页面元素可能不可见。
  if (action === "scroll") {
    // 新增代码+ChromeExtensionStage6: 把目标滚动到视口中央；若没有这行代码，后续点击可能看不见目标。
    targetNode.scrollIntoView({ block: "center", inline: "center" });
    // 新增代码+ChromeExtensionStage6: 返回滚动结果摘要；若没有这行代码，调用方不知道滚动已完成。
    return actionObservation("scroll 完成");
  }
  // 新增代码+ChromeExtensionStage6: 未知动作抛出清楚错误；若没有这行代码，扩展会静默忽略新动作。
  throw new Error(`不支持的动作：${action}`);
}

// 新增代码+ChromeExtensionStage5: 响应 background 的页面只读请求；若没有这行代码，background 无法从页面拿到 DOM 摘要。
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // 新增代码+ChromeExtensionStage5: 明确本阶段不读取 sender；若没有这行代码，未使用参数会干扰阅读。
  void sender;
  // 新增代码+ChromeExtensionStage5: 只处理 collect_visible_page；若没有这行代码，未知消息可能被误处理。
  if (message && message.action === "collect_visible_page") {
    // 新增代码+ChromeExtensionStage5: 返回可见文本和元素摘要；若没有这行代码，read_page 没有内容。
    sendResponse({ visibleText: collectVisibleText(), elements: collectElementSummaries() });
    // 新增代码+ChromeExtensionStage5: 表示消息已处理；若没有这行代码，Chrome 可能继续寻找其他监听器。
    return true;
  }
  // 新增代码+ChromeExtensionStage6: 处理 background 下发的页面动作命令；若没有这行代码，插件写动作无法进入页面上下文。
  if (message && message.action === "perform_browser_action") {
    // 新增代码+ChromeExtensionStage6: 异步执行页面动作并返回结果；若没有这行代码，sendResponse 不能等待 Promise。
    performBrowserAction(message.command || {}).then((result) => {
      // 新增代码+ChromeExtensionStage6: 动作成功时返回结果；若没有这行代码，background 无法回传 host。
      sendResponse({ ok: true, result });
    }).catch((error) => {
      // 新增代码+ChromeExtensionStage6: 动作失败时返回错误文本；若没有这行代码，provider 只会等到超时。
      sendResponse({ ok: false, error: String(error && error.message ? error.message : error) });
    });
    // 新增代码+ChromeExtensionStage6: 告诉 Chrome 本监听器会异步响应；若没有这行代码，sendResponse 可能失效。
    return true;
  }
  // 新增代码+ChromeExtensionStage5: 未知消息不处理；若没有这行代码，函数没有明确返回。
  return false;
});
