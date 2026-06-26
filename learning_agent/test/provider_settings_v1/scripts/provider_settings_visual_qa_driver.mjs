import { Buffer } from "node:buffer"; // 新增代码+ProviderSettingsVisualQA：导入 Buffer 用于写入截图 bytes；如果没有这行，base64 截图无法保存成 PNG。
import fs from "node:fs/promises"; // 新增代码+ProviderSettingsVisualQA：导入异步文件 API；如果没有这行，截图和结果 JSON 无法落盘。
import path from "node:path"; // 新增代码+ProviderSettingsVisualQA：导入路径工具；如果没有这行，Windows 路径拼接会脆弱。

const args = new Map(process.argv.slice(2).map((item) => { const [key, value = ""] = item.split("="); return [key.replace(/^--/, ""), value]; })); // 新增代码+ProviderSettingsVisualQA：解析 --key=value 参数；如果没有这行，driver 不知道 CDP 端口和证据目录。
const cdpPort = Number(args.get("cdpPort") ?? "9223"); // 新增代码+ProviderSettingsVisualQA：读取 CDP 端口；如果没有这行，脚本无法连接 Electron 调试端口。
const evidenceDir = path.resolve(args.get("evidenceDir") ?? "learning_agent/test/provider_settings_v1/task09_visual_qa"); // 新增代码+ProviderSettingsVisualQA：读取证据目录；如果没有这行，截图会保存到不可预测位置。
let commandId = 0; // 新增代码+ProviderSettingsVisualQA：保存 CDP 命令递增 id；如果没有这行，请求和响应无法对应。
const pendingCommands = new Map(); // 新增代码+ProviderSettingsVisualQA：保存等待响应的 CDP promise；如果没有这行，异步响应无法唤醒调用方。
const qaResult = { ok: false, screenshots: [], assertions: [], viewportResults: [] }; // 新增代码+ProviderSettingsVisualQA：保存最终 QA 结果；如果没有这行，release gate 缺少机器可读证据。

function assertQa(condition, label, details = {}) { // 新增代码+ProviderSettingsVisualQA：函数段开始，记录并执行断言；如果没有这段，视觉 QA 只会截图不会失败。
  qaResult.assertions.push({ label, passed: Boolean(condition), details }); // 新增代码+ProviderSettingsVisualQA：把断言写入结果对象；如果没有这行，失败原因无法追踪。
  if (!condition) { // 新增代码+ProviderSettingsVisualQA：检查断言是否失败；如果没有这行，失败不会终止脚本。
    throw new Error(`Visual QA assertion failed: ${label}`); // 新增代码+ProviderSettingsVisualQA：失败时抛出清楚错误；如果没有这行，CI 会误判通过。
  } // 新增代码+ProviderSettingsVisualQA：断言失败分支结束；如果没有这行，条件块语法不完整。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，assertQa 到此结束；如果没有这行，函数语法不完整。

async function sleep(ms) { // 新增代码+ProviderSettingsVisualQA：函数段开始，等待异步 UI 更新；如果没有这段，点击后立即断言会不稳定。
  await new Promise((resolve) => setTimeout(resolve, ms)); // 新增代码+ProviderSettingsVisualQA：等待指定毫秒；如果没有这行，函数不会真的暂停。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，sleep 到此结束；如果没有这行，函数语法不完整。

async function waitForCdpTarget() { // 新增代码+ProviderSettingsVisualQA：函数段开始，等待 Electron 暴露 CDP target；如果没有这段，Electron 尚未启动时请求会失败。
  for (let attempt = 0; attempt < 80; attempt += 1) { // 新增代码+ProviderSettingsVisualQA：最多等待约 40 秒；如果没有这行，启动慢时脚本会过早失败。
    try { // 新增代码+ProviderSettingsVisualQA：捕获 CDP target 查询失败；如果没有这行，第一次连接失败会直接退出。
      const response = await fetch(`http://127.0.0.1:${cdpPort}/json/list`); // 新增代码+ProviderSettingsVisualQA：查询 CDP target 列表；如果没有这行，脚本拿不到 WebSocket 地址。
      const targets = await response.json(); // 新增代码+ProviderSettingsVisualQA：解析 target JSON；如果没有这行，后续无法选择页面。
      const page = targets.find((target) => target.type === "page" && target.webSocketDebuggerUrl); // 新增代码+ProviderSettingsVisualQA：选择 Electron renderer 页面；如果没有这行，可能连到错误 target。
      if (page) { // 新增代码+ProviderSettingsVisualQA：确认找到了页面；如果没有这行，空 target 会继续出错。
        return page.webSocketDebuggerUrl; // 新增代码+ProviderSettingsVisualQA：返回 WebSocket 调试地址；如果没有这行，调用方无法连接。
      } // 新增代码+ProviderSettingsVisualQA：找到页面分支结束；如果没有这行，条件块语法不完整。
    } catch { // 新增代码+ProviderSettingsVisualQA：忽略启动初期连接失败；如果没有这行，CDP 端口未就绪会打断流程。
      await sleep(500); // 新增代码+ProviderSettingsVisualQA：等待后重试；如果没有这行，会忙等浪费 CPU。
      continue; // 新增代码+ProviderSettingsVisualQA：进入下一轮重试；如果没有这行，catch 后会继续执行额外等待。
    } // 新增代码+ProviderSettingsVisualQA：连接失败处理结束；如果没有这行，try/catch 语法不完整。
    await sleep(500); // 新增代码+ProviderSettingsVisualQA：target 暂未出现时等待；如果没有这行，会高频请求 CDP。
  } // 新增代码+ProviderSettingsVisualQA：CDP target 等待循环结束；如果没有这行，for 循环语法不完整。
  throw new Error("Electron CDP target was not available."); // 新增代码+ProviderSettingsVisualQA：超时后抛错；如果没有这行，调用方会拿到 undefined 地址。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，waitForCdpTarget 到此结束；如果没有这行，函数语法不完整。

function connectCdp(webSocketUrl) { // 新增代码+ProviderSettingsVisualQA：函数段开始，建立 CDP WebSocket；如果没有这段，脚本无法操控 Electron。
  const socket = new WebSocket(webSocketUrl); // 新增代码+ProviderSettingsVisualQA：连接 Electron CDP；如果没有这行，后续命令没有传输通道。
  socket.addEventListener("message", (event) => { const message = JSON.parse(event.data); if (message.id && pendingCommands.has(message.id)) { pendingCommands.get(message.id).resolve(message); pendingCommands.delete(message.id); } }); // 新增代码+ProviderSettingsVisualQA：分发 CDP 响应到对应 promise；如果没有这行，sendCdp 会一直等待。
  return new Promise((resolve, reject) => { socket.addEventListener("open", () => resolve(socket)); socket.addEventListener("error", reject); }); // 新增代码+ProviderSettingsVisualQA：等待 WebSocket 打开；如果没有这行，调用方可能在连接前发送命令。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，connectCdp 到此结束；如果没有这行，函数语法不完整。

function sendCdp(socket, method, params = {}) { // 新增代码+ProviderSettingsVisualQA：函数段开始，发送 CDP 命令；如果没有这段，所有调用都要重复 id/promise 逻辑。
  commandId += 1; // 新增代码+ProviderSettingsVisualQA：递增命令 id；如果没有这行，多条命令会冲突。
  const id = commandId; // 新增代码+ProviderSettingsVisualQA：固定当前命令 id；如果没有这行，闭包里 id 会不清晰。
  const payload = JSON.stringify({ id, method, params }); // 新增代码+ProviderSettingsVisualQA：构造 CDP JSON；如果没有这行，WebSocket 无法发送对象。
  const promise = new Promise((resolve, reject) => pendingCommands.set(id, { resolve, reject })); // 新增代码+ProviderSettingsVisualQA：保存等待响应的 promise；如果没有这行，调用方拿不到结果。
  socket.send(payload); // 新增代码+ProviderSettingsVisualQA：发送命令到 Electron；如果没有这行，CDP 不会执行任何动作。
  return promise.then((message) => { if (message.error) { throw new Error(`${method}: ${message.error.message}`); } return message.result ?? {}; }); // 新增代码+ProviderSettingsVisualQA：处理成功或错误响应；如果没有这行，CDP 错误会被吞掉。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，sendCdp 到此结束；如果没有这行，函数语法不完整。

async function evaluate(socket, expression) { // 新增代码+ProviderSettingsVisualQA：函数段开始，在 renderer 中执行 JS；如果没有这段，脚本无法点击或读取 DOM。
  const result = await sendCdp(socket, "Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }); // 新增代码+ProviderSettingsVisualQA：执行表达式并返回值；如果没有这行，DOM 状态无法读取。
  return result.result?.value; // 新增代码+ProviderSettingsVisualQA：返回普通 JS 值；如果没有这行，调用方会拿到 CDP 包装对象。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，evaluate 到此结束；如果没有这行，函数语法不完整。

async function waitForExpression(socket, expression, label) { // 新增代码+ProviderSettingsVisualQA：函数段开始，等待 DOM 条件成立；如果没有这段，点击后的异步加载会不稳定。
  for (let attempt = 0; attempt < 80; attempt += 1) { // 新增代码+ProviderSettingsVisualQA：最多等待约 24 秒；如果没有这行，条件永远不成立时不会超时。
    if (await evaluate(socket, expression)) { // 新增代码+ProviderSettingsVisualQA：检查表达式是否为真；如果没有这行，等待逻辑没有判断。
      return; // 新增代码+ProviderSettingsVisualQA：条件满足时返回；如果没有这行，会继续无意义等待。
    } // 新增代码+ProviderSettingsVisualQA：条件满足分支结束；如果没有这行，条件块语法不完整。
    await sleep(300); // 新增代码+ProviderSettingsVisualQA：短暂等待后重试；如果没有这行，会忙等。
  } // 新增代码+ProviderSettingsVisualQA：等待循环结束；如果没有这行，for 循环语法不完整。
  throw new Error(`Timed out waiting for ${label}`); // 新增代码+ProviderSettingsVisualQA：超时后报告等待目标；如果没有这行，失败不知原因。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，waitForExpression 到此结束；如果没有这行，函数语法不完整。

async function setViewport(socket, width, height) { // 新增代码+ProviderSettingsVisualQA：函数段开始，设置截图视口；如果没有这段，多尺寸验收无法执行。
  await sendCdp(socket, "Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false }); // 修改代码+ProviderSettingsVisualQA：按桌面窗口缩窄方式设置视口；如果没有这行，390px 验收会被浏览器移动缩放成 980px 而漏掉真实溢出。
  qaResult.viewportResults.push({ width, height }); // 新增代码+ProviderSettingsVisualQA：记录已测试视口；如果没有这行，结果 JSON 不知道覆盖了哪些尺寸。
  await sleep(400); // 新增代码+ProviderSettingsVisualQA：等待布局响应视口变化；如果没有这行，截图可能捕获旧布局。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，setViewport 到此结束；如果没有这行，函数语法不完整。

async function capture(socket, fileName) { // 新增代码+ProviderSettingsVisualQA：函数段开始，捕获当前页面截图；如果没有这段，视觉验收没有图片证据。
  const result = await sendCdp(socket, "Page.captureScreenshot", { format: "png", captureBeyondViewport: false }); // 新增代码+ProviderSettingsVisualQA：调用 CDP 截图；如果没有这行，无法获取 PNG。
  const filePath = path.join(evidenceDir, fileName); // 新增代码+ProviderSettingsVisualQA：生成截图路径；如果没有这行，截图文件名不稳定。
  await fs.writeFile(filePath, Buffer.from(result.data, "base64")); // 新增代码+ProviderSettingsVisualQA：写入 PNG 文件；如果没有这行，截图不会落盘。
  qaResult.screenshots.push(filePath); // 新增代码+ProviderSettingsVisualQA：记录截图路径；如果没有这行，结果 JSON 找不到证据。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，capture 到此结束；如果没有这行，函数语法不完整。

async function clickButtonByText(socket, text) { // 新增代码+ProviderSettingsVisualQA：函数段开始，按按钮文本点击；如果没有这段，脚本会依赖脆弱坐标。
  await evaluate(socket, `(() => { const button = [...document.querySelectorAll('button')].find((item) => item.innerText.trim().includes(${JSON.stringify(text)})); if (!button) return false; button.click(); return true; })()`); // 新增代码+ProviderSettingsVisualQA：在 DOM 中查找并点击按钮；如果没有这行，设置/保存/模型按钮无法自动操作。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，clickButtonByText 到此结束；如果没有这行，函数语法不完整。

async function run() { // 新增代码+ProviderSettingsVisualQA：函数段开始，执行完整 Provider Settings 视觉 QA；如果没有这段，脚本没有主流程。
  await fs.mkdir(evidenceDir, { recursive: true }); // 新增代码+ProviderSettingsVisualQA：确保证据目录存在；如果没有这行，截图保存会失败。
  const webSocketUrl = await waitForCdpTarget(); // 新增代码+ProviderSettingsVisualQA：等待并获取 Electron CDP 地址；如果没有这行，脚本无法连接窗口。
  const socket = await connectCdp(webSocketUrl); // 新增代码+ProviderSettingsVisualQA：连接 CDP WebSocket；如果没有这行，后续无法控制页面。
  await sendCdp(socket, "Page.enable"); // 新增代码+ProviderSettingsVisualQA：启用 Page domain；如果没有这行，截图等页面能力可能不可用。
  await sendCdp(socket, "Runtime.enable"); // 新增代码+ProviderSettingsVisualQA：启用 Runtime domain；如果没有这行，DOM 表达式可能不可用。
  await waitForExpression(socket, "document.body.innerText.includes('设置')", "main shell settings button"); // 新增代码+ProviderSettingsVisualQA：等待主壳加载；如果没有这行，点击设置会找不到按钮。
  await setViewport(socket, 1365, 768); // 新增代码+ProviderSettingsVisualQA：切到桌面验收尺寸；如果没有这行，默认 provider 截图尺寸不可控。
  await clickButtonByText(socket, "设置"); // 新增代码+ProviderSettingsVisualQA：点击左下角设置；如果没有这行，设置弹窗不会打开。
  await waitForExpression(socket, "Boolean(document.querySelector('.settings-dialog'))", "settings dialog"); // 新增代码+ProviderSettingsVisualQA：等待设置弹窗出现；如果没有这行，后续断言会读到空 DOM。
  await waitForExpression(socket, "document.querySelectorAll('.settings-provider-row:not(.settings-provider-custom-row)').length >= 5", "provider rows"); // 新增代码+ProviderSettingsVisualQA：等待至少五个 provider 行；如果没有这行，provider catalog 加载失败不会被发现。
  await evaluate(socket, `(() => { const button = document.querySelector('[data-testid="provider-action-openai"]'); if (button?.innerText.includes('断开')) { button.click(); return true; } return false; })()`); // 新增代码+ProviderSettingsVisualQA：如果上轮验收留下已连接 OpenAI，先断开恢复基线；如果没有这行，密码框断言可能被已连接状态跳过。
  await waitForExpression(socket, "document.querySelector('[data-testid=\"provider-action-openai\"]')?.innerText.includes('连接')", "OpenAI disconnected baseline"); // 新增代码+ProviderSettingsVisualQA：等待 OpenAI 回到可连接状态；如果没有这行，后续点击可能打到处理中或断开按钮。
  const providerFacts = await evaluate(socket, `(() => ({ rows: document.querySelectorAll('.settings-provider-row:not(.settings-provider-custom-row)').length, customVisible: Boolean(document.querySelector('[data-testid="provider-custom-cta"]')), copilotDisabled: document.querySelector('[data-testid="provider-action-github-copilot"]')?.disabled === true, rawSecretInText: document.body.innerText.includes('unit-test-secret-value') }))()`); // 新增代码+ProviderSettingsVisualQA：读取 provider 页关键事实；如果没有这行，QA 无法断言列表和泄密状态。
  assertQa(providerFacts.rows >= 5, "provider row count is at least 5", providerFacts); // 新增代码+ProviderSettingsVisualQA：断言 provider 数量；如果没有这行，缺行仍会通过。
  assertQa(providerFacts.customVisible, "custom provider CTA is visible", providerFacts); // 新增代码+ProviderSettingsVisualQA：断言自定义入口可见；如果没有这行，Task 7 入口缺失不会失败。
  assertQa(providerFacts.copilotDisabled, "GitHub Copilot action is disabled in V1", providerFacts); // 新增代码+ProviderSettingsVisualQA：断言 Copilot 禁用；如果没有这行，未支持入口可能被误点。
  assertQa(!providerFacts.rawSecretInText, "no raw unit-test secret in provider page text", providerFacts); // 新增代码+ProviderSettingsVisualQA：断言页面文本不含测试密钥；如果没有这行，明显泄密不会失败。
  await capture(socket, "provider_default_1365x768.png"); // 新增代码+ProviderSettingsVisualQA：保存默认 provider 页截图；如果没有这行，默认状态没有视觉证据。
  await evaluate(socket, `(() => { const button = document.querySelector('[data-testid="provider-action-openai"]'); if (button && !button.disabled && button.innerText.includes('连接')) { button.click(); return true; } return false; })()`); // 新增代码+ProviderSettingsVisualQA：打开 OpenAI 连接弹窗；如果没有这行，API key password 断言没有对象。
  await waitForExpression(socket, "Boolean(document.querySelector('.provider-connect-dialog'))", "OpenAI connect dialog"); // 修改代码+ProviderSettingsVisualQA：等待连接弹窗真实出现；如果没有这行，已连接状态可能绕过密码框验收。
  const inputType = await evaluate(socket, "document.querySelector('.provider-connect-dialog input[type=password]')?.type || 'missing-password-input'"); // 修改代码+ProviderSettingsVisualQA：读取 API key 输入类型且不接受已连接兜底；如果没有这行，密码框安全性无法严格验证。
  assertQa(inputType === "password", "API key input has password type", { inputType }); // 修改代码+ProviderSettingsVisualQA：严格断言 API key 输入为 password；如果没有这行，明文输入或跳过弹窗都会误过。
  await evaluate(socket, `(() => { const dialog = document.querySelector('.provider-connect-dialog'); if (!dialog) return false; const input = dialog.querySelector('input[type=password]'); const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; setter.call(input, 'unit-test-secret-value'); input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true })); dialog.querySelector('button[type=submit]').click(); return true; })()`); // 新增代码+ProviderSettingsVisualQA：输入测试 key 并提交；如果没有这行，连接成功视觉状态无法捕获。
  await sleep(1200); // 新增代码+ProviderSettingsVisualQA：等待 bridge 保存并刷新 catalog；如果没有这行，截图可能仍是提交中。
  await capture(socket, "provider_connected_openai.png"); // 新增代码+ProviderSettingsVisualQA：保存连接后 provider 页截图；如果没有这行，已连接状态没有视觉证据。
  const leakFacts = await evaluate(socket, `(() => ({ textLeak: document.body.innerText.includes('unit-test-secret-value'), htmlLeak: document.documentElement.outerHTML.includes('unit-test-secret-value') }))()`); // 新增代码+ProviderSettingsVisualQA：检查 DOM 文本和 HTML 是否泄露测试 key；如果没有这行，提交后泄密无法发现。
  assertQa(!leakFacts.textLeak && !leakFacts.htmlLeak, "no raw secret appears in DOM text or HTML after submit", leakFacts); // 新增代码+ProviderSettingsVisualQA：断言提交后 DOM 不含 raw secret；如果没有这行，密钥泄露仍会通过。
  await evaluate(socket, "document.querySelector('[data-testid=\"provider-custom-cta\"]')?.click()"); // 新增代码+ProviderSettingsVisualQA：打开自定义 provider 弹窗；如果没有这行，Task 7 弹窗没有截图证据。
  await waitForExpression(socket, "document.body.innerText.includes('自定义提供商') && Boolean(document.querySelector('.custom-provider-dialog'))", "custom provider dialog"); // 修改代码+ProviderSettingsVisualQA：等待自定义弹窗出现且只返回布尔值；如果没有这行，CDP 会尝试克隆 DOM 元素并因对象链过深失败。
  await clickButtonByText(socket, "保存"); // 新增代码+ProviderSettingsVisualQA：触发空表单校验；如果没有这行，校验文案不会进入截图。
  await waitForExpression(socket, "document.body.innerText.includes('Provider ID 只能使用小写字母、数字和短横线')", "custom provider validation copy"); // 新增代码+ProviderSettingsVisualQA：等待校验文案出现；如果没有这行，蓝图错误文案缺失不会失败。
  await capture(socket, "custom_provider_dialog.png"); // 新增代码+ProviderSettingsVisualQA：保存自定义 provider 弹窗截图；如果没有这行，字段和 spacing 没有视觉证据。
  await evaluate(socket, "document.querySelector('.provider-connect-close')?.click()"); // 新增代码+ProviderSettingsVisualQA：关闭自定义 provider 弹窗；如果没有这行，无法切换模型页。
  await clickButtonByText(socket, "模型"); // 新增代码+ProviderSettingsVisualQA：打开模型页签；如果没有这行，模型面板没有截图证据。
  await waitForExpression(socket, "Boolean(document.querySelector('.settings-model-group'))", "models group"); // 新增代码+ProviderSettingsVisualQA：等待至少一个模型分组；如果没有这行，模型页空态会误通过。
  await capture(socket, "models_tab.png"); // 新增代码+ProviderSettingsVisualQA：保存模型页截图；如果没有这行，switch 和行布局没有视觉证据。
  await setViewport(socket, 980, 720); // 新增代码+ProviderSettingsVisualQA：切到中等弹窗尺寸；如果没有这行，980x720 验收缺失。
  await capture(socket, "models_tab_980x720.png"); // 新增代码+ProviderSettingsVisualQA：保存 980x720 模型页截图；如果没有这行，中等尺寸没有证据。
  await clickButtonByText(socket, "提供商"); // 新增代码+ProviderSettingsVisualQA：回到 provider 页；如果没有这行，移动截图不会覆盖 provider 列表。
  await setViewport(socket, 390, 844); // 新增代码+ProviderSettingsVisualQA：切到移动宽度；如果没有这行，移动横向溢出无法测试。
  await waitForExpression(socket, "Boolean(document.querySelector('.settings-dialog'))", "mobile settings dialog"); // 新增代码+ProviderSettingsVisualQA：等待移动布局稳定；如果没有这行，截图可能在重排中。
  const mobileFacts = await evaluate(socket, `(() => ({ scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth, overflowOk: document.documentElement.scrollWidth <= window.innerWidth + 2 }))()`); // 新增代码+ProviderSettingsVisualQA：读取移动横向滚动事实；如果没有这行，移动溢出无法断言。
  assertQa(mobileFacts.overflowOk, "mobile document has no horizontal overflow", mobileFacts); // 新增代码+ProviderSettingsVisualQA：断言移动宽度无横向溢出；如果没有这行，移动布局重叠不会失败。
  await capture(socket, "provider_mobile_390x844.png"); // 新增代码+ProviderSettingsVisualQA：保存移动 provider 页截图；如果没有这行，移动布局没有视觉证据。
  qaResult.ok = true; // 新增代码+ProviderSettingsVisualQA：标记 QA 成功；如果没有这行，结果 JSON 不知道流程通过。
  socket.close(); // 新增代码+ProviderSettingsVisualQA：关闭 CDP 连接；如果没有这行，脚本退出前会残留连接。
} // 新增代码+ProviderSettingsVisualQA：函数段结束，run 到此结束；如果没有这行，函数语法不完整。

try { // 新增代码+ProviderSettingsVisualQA：主入口开始，捕获所有失败；如果没有这段，失败结果 JSON 不会写入。
  await run(); // 新增代码+ProviderSettingsVisualQA：执行视觉 QA 主流程；如果没有这行，脚本不会做任何事。
} catch (error) { // 新增代码+ProviderSettingsVisualQA：捕获主流程异常；如果没有这行，失败无法结构化记录。
  qaResult.ok = false; // 新增代码+ProviderSettingsVisualQA：标记 QA 失败；如果没有这行，失败结果可能误认为通过。
  qaResult.error = error instanceof Error ? error.message : String(error); // 新增代码+ProviderSettingsVisualQA：保存错误消息；如果没有这行，排查不知道失败原因。
  process.exitCode = 1; // 新增代码+ProviderSettingsVisualQA：设置失败退出码；如果没有这行，调用脚本会误判成功。
} finally { // 新增代码+ProviderSettingsVisualQA：最终写入证据；如果没有这段，成功或失败都缺少结果 JSON。
  await fs.mkdir(evidenceDir, { recursive: true }); // 新增代码+ProviderSettingsVisualQA：确保结果目录存在；如果没有这行，写 JSON 可能失败。
  await fs.writeFile(path.join(evidenceDir, "provider_settings_visual_qa_result.json"), JSON.stringify(qaResult, null, 2), "utf-8"); // 新增代码+ProviderSettingsVisualQA：写入机器可读结果；如果没有这行，Task 9 证据不完整。
} // 新增代码+ProviderSettingsVisualQA：主入口结束；如果没有这行，try/catch/finally 语法不完整。
