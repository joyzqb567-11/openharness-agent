import { Buffer } from "node:buffer"; // 新增代码+ProviderSettingsVisualQA：导入 Buffer 用于写入截图 bytes；如果没有这行，base64 截图无法保存成 PNG。
import fs from "node:fs/promises"; // 新增代码+ProviderSettingsVisualQA：导入异步文件 API；如果没有这行，截图和结果 JSON 无法落盘。
import path from "node:path"; // 新增代码+ProviderSettingsVisualQA：导入路径工具；如果没有这行，Windows 路径拼接会脆弱。

const args = new Map(process.argv.slice(2).map((item) => { const [key, value = ""] = item.split("="); return [key.replace(/^--/, ""), value]; })); // 新增代码+ProviderSettingsVisualQA：解析 --key=value 参数；如果没有这行，driver 不知道 CDP 端口和证据目录。
const cdpPort = Number(args.get("cdpPort") ?? "9223"); // 新增代码+ProviderSettingsVisualQA：读取 CDP 端口；如果没有这行，脚本无法连接 Electron 调试端口。
const evidenceDir = path.resolve(args.get("evidenceDir") ?? "learning_agent/test/provider_settings_v2_openai_connect/task08_visual_qa"); // 修改代码+OpenAIConnectVisualQA：读取 OpenAI connect 证据目录；如果没有这行，截图会保存到不可预测位置。
const bridgeUrl = args.get("bridgeUrl") ?? "http://127.0.0.1:8776"; // 新增代码+OpenAIConnectVisualQA：读取 GUI bridge URL；如果没有这行，driver 无法模拟 mock 授权完成。
const token = args.get("token") ?? "openharness-desktop-dev-token"; // 新增代码+OpenAIConnectVisualQA：读取 GUI bridge token；如果没有这行，driver 调用 complete/status 会被拒绝。
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

async function clickByTestId(socket, testId) { // 新增代码+OpenAIConnectVisualQA：函数段开始，按 data-testid 点击元素；如果没有这段，OpenAI 方法选择会依赖脆弱文本或坐标。
  const clicked = await evaluate(socket, `(() => { const element = document.querySelector(${JSON.stringify(`[data-testid="${testId}"]`)}); if (!element) return false; element.click(); return true; })()`); // 新增代码+OpenAIConnectVisualQA：在 DOM 中查找并点击目标；如果没有这行，driver 无法稳定点击 provider 或方法按钮。
  assertQa(clicked, `clicked ${testId}`, { testId }); // 新增代码+OpenAIConnectVisualQA：断言点击目标存在；如果没有这行，缺按钮时脚本可能继续误判。
} // 新增代码+OpenAIConnectVisualQA：函数段结束，clickByTestId 到此结束；如果没有这行，函数语法不完整。

async function postBridge(pathName, payload) { // 新增代码+OpenAIConnectVisualQA：函数段开始，向 GUI bridge 发送 JSON POST；如果没有这段，driver 无法模拟 mock 授权完成。
  const response = await fetch(`${bridgeUrl}${pathName}`, { method: "POST", headers: { "Content-Type": "application/json", "X-OpenHarness-Desktop-Token": token }, body: JSON.stringify(payload) }); // 新增代码+OpenAIConnectVisualQA：发送带 token 的 POST；如果没有这行，bridge 会拒绝或收不到 body。
  const data = await response.json(); // 新增代码+OpenAIConnectVisualQA：解析 bridge JSON 响应；如果没有这行，断言无法读取 attempt 状态。
  assertQa(response.ok, `bridge POST ${pathName} ok`, { status: response.status, data }); // 新增代码+OpenAIConnectVisualQA：断言 bridge POST 成功；如果没有这行，mock 完成失败也可能继续截图。
  return data; // 新增代码+OpenAIConnectVisualQA：返回响应数据；如果没有这行，调用方拿不到 attempt payload。
} // 新增代码+OpenAIConnectVisualQA：函数段结束，postBridge 到此结束；如果没有这行，函数语法不完整。

async function getBridge(pathName) { // 新增代码+OpenAIConnectVisualQA：函数段开始，向 GUI bridge 发送 JSON GET；如果没有这段，driver 无法确认取消后的状态。
  const response = await fetch(`${bridgeUrl}${pathName}`, { headers: { "X-OpenHarness-Desktop-Token": token } }); // 新增代码+OpenAIConnectVisualQA：发送带 token 的 GET；如果没有这行，status 请求会被 401 拒绝。
  const data = await response.json(); // 新增代码+OpenAIConnectVisualQA：解析 bridge JSON 响应；如果没有这行，断言无法读取状态。
  assertQa(response.ok, `bridge GET ${pathName} ok`, { status: response.status, data }); // 新增代码+OpenAIConnectVisualQA：断言 bridge GET 成功；如果没有这行，错误状态可能被忽略。
  return data; // 新增代码+OpenAIConnectVisualQA：返回响应数据；如果没有这行，调用方无法断言 status。
} // 新增代码+OpenAIConnectVisualQA：函数段结束，getBridge 到此结束；如果没有这行，函数语法不完整。

async function run() { // 修改代码+OpenAIConnectVisualQA：函数段开始，执行 OpenAI 连接向导视觉 QA；如果没有这段，脚本没有主流程。
  await fs.mkdir(evidenceDir, { recursive: true }); // 修改代码+OpenAIConnectVisualQA：确保证据目录存在；如果没有这行，截图保存会失败。
  const webSocketUrl = await waitForCdpTarget(); // 修改代码+OpenAIConnectVisualQA：等待并获取 Electron CDP 地址；如果没有这行，脚本无法连接窗口。
  const socket = await connectCdp(webSocketUrl); // 修改代码+OpenAIConnectVisualQA：连接 CDP WebSocket；如果没有这行，后续无法控制页面。
  await sendCdp(socket, "Page.enable"); // 修改代码+OpenAIConnectVisualQA：启用 Page domain；如果没有这行，截图等页面能力可能不可用。
  await sendCdp(socket, "Runtime.enable"); // 修改代码+OpenAIConnectVisualQA：启用 Runtime domain；如果没有这行，DOM 表达式可能不可用。
  await waitForExpression(socket, "document.body.innerText.includes('设置')", "main shell settings button"); // 修改代码+OpenAIConnectVisualQA：等待主壳加载；如果没有这行，点击设置会找不到按钮。
  await setViewport(socket, 1365, 768); // 修改代码+OpenAIConnectVisualQA：切到桌面验收尺寸；如果没有这行，默认截图尺寸不可控。
  await clickButtonByText(socket, "设置"); // 修改代码+OpenAIConnectVisualQA：点击左下角设置；如果没有这行，设置弹窗不会打开。
  await waitForExpression(socket, "Boolean(document.querySelector('.settings-dialog'))", "settings dialog"); // 修改代码+OpenAIConnectVisualQA：等待设置弹窗出现；如果没有这行，后续断言会读到空 DOM。
  await waitForExpression(socket, "document.querySelectorAll('.settings-provider-row:not(.settings-provider-custom-row)').length >= 5", "provider rows"); // 修改代码+OpenAIConnectVisualQA：等待 provider 行加载；如果没有这行，provider catalog 加载失败不会被发现。
  await evaluate(socket, `(() => { const button = document.querySelector('[data-testid="provider-action-openai"]'); if (button?.innerText.includes('断开')) { button.click(); return true; } return false; })()`); // 修改代码+OpenAIConnectVisualQA：如果上轮留下 OpenAI 连接，先断开恢复基线；如果没有这行，方法选择器可能被断开按钮跳过。
  await waitForExpression(socket, "document.querySelector('[data-testid=\"provider-action-openai\"]')?.innerText.includes('连接')", "OpenAI disconnected baseline"); // 修改代码+OpenAIConnectVisualQA：等待 OpenAI 回到可连接状态；如果没有这行，后续点击可能打到处理中。
  await clickByTestId(socket, "provider-action-openai"); // 修改代码+OpenAIConnectVisualQA：打开 OpenAI 连接弹窗；如果没有这行，方法选择器没有截图对象。
  await waitForExpression(socket, "document.body.innerText.includes('选择 OpenAI 的登录方式')", "OpenAI method picker"); // 新增代码+OpenAIConnectVisualQA：等待方法选择第一屏；如果没有这行，旧 API key 表单回退不会被发现。
  const pickerFacts = await evaluate(socket, `(() => ({ hasBrowser: document.body.innerText.includes('ChatGPT Pro/Plus (browser)'), hasHeadless: document.body.innerText.includes('ChatGPT Pro/Plus (headless)'), hasApiKey: document.body.innerText.includes('API 密钥'), passwordVisible: Boolean(document.querySelector('.provider-connect-dialog input[type=password]')), secretRefLeak: document.documentElement.outerHTML.includes('secret_ref') }))()`); // 新增代码+OpenAIConnectVisualQA：读取方法选择器关键事实；如果没有这行，方法缺失或泄露无法断言。
  qaResult.methodCount = [pickerFacts.hasBrowser, pickerFacts.hasHeadless, pickerFacts.hasApiKey].filter(Boolean).length; // 新增代码+OpenAIConnectVisualQA：把三种方法数量写入顶层结果；如果没有这行，Task 8 机器可读验收缺少 methodCount。
  assertQa(pickerFacts.hasBrowser && pickerFacts.hasHeadless && pickerFacts.hasApiKey, "OpenAI method picker shows browser headless and API key", pickerFacts); // 新增代码+OpenAIConnectVisualQA：断言三种方法可见；如果没有这行，OpenCode 风格入口缺失也会通过。
  assertQa(!pickerFacts.passwordVisible, "method picker does not show password field initially", pickerFacts); // 新增代码+OpenAIConnectVisualQA：断言第一屏不显示 API key 密码框；如果没有这行，旧 UI 回退可能漏过。
  assertQa(!pickerFacts.secretRefLeak, "method picker does not expose secret locator fields", pickerFacts); // 修改代码+OpenAIConnectVisualQA：断言方法选择器不泄露密钥定位字段且结果标签不写危险字段名；如果没有这行，renderer 泄露或运行 JSON 字段名污染可能漏过。
  await capture(socket, "openai_method_picker_1365x768.png"); // 新增代码+OpenAIConnectVisualQA：保存桌面方法选择截图；如果没有这行，第一屏没有视觉证据。
  await clickByTestId(socket, "provider-auth-method-api-key"); // 新增代码+OpenAIConnectVisualQA：进入 API Key 步骤；如果没有这行，真实 GUI 验收缺少 API Key 表单证据。
  await waitForExpression(socket, "document.querySelector('.provider-connect-dialog input[type=password]') !== null", "OpenAI API key password step"); // 新增代码+OpenAIConnectVisualQA：等待密码框出现；如果没有这行，截图可能仍停留在方法选择页。
  const apiKeyFacts = await evaluate(socket, `(() => ({ inputType: document.querySelector('.provider-connect-dialog input')?.type || '', hasRequiredMessage: document.body.innerText.includes('API Key') || document.body.innerText.includes('API 密钥'), submitDisabled: Boolean(document.querySelector('.settings-provider-primary-button[type="submit"]')?.disabled), tokenLeak: /refresh_token|access_token|id_token|secret_ref/i.test(document.documentElement.outerHTML) }))()`); // 修改代码+OpenAIConnectVisualQA：读取 API Key 步骤事实并使用真实提交按钮选择器；如果没有这行，密码框类型和泄露状态无法进入结果 JSON。
  qaResult.inputType = apiKeyFacts.inputType; // 新增代码+OpenAIConnectVisualQA：把密码框类型写入顶层结果；如果没有这行，Task 8 机器可读验收缺少 inputType。
  assertQa(apiKeyFacts.inputType === "password", "API key step uses password input", apiKeyFacts); // 新增代码+OpenAIConnectVisualQA：断言 API Key 输入框是密码框；如果没有这行，明文密钥输入会漏过。
  assertQa(apiKeyFacts.submitDisabled, "API key step keeps empty submit disabled", apiKeyFacts); // 新增代码+OpenAIConnectVisualQA：断言空值不能提交；如果没有这行，空密钥可能被送到后端。
  assertQa(!apiKeyFacts.tokenLeak, "API key step has no token or secret locator leak", apiKeyFacts); // 新增代码+OpenAIConnectVisualQA：断言 API Key 步骤没有 token 或密钥定位字段；如果没有这行，表单 DOM 泄露不会失败。
  await capture(socket, "openai_api_key_step_1365x768.png"); // 新增代码+OpenAIConnectVisualQA：保存 API Key 步骤截图；如果没有这行，Task 10 缺少肉眼验收图片。
  await clickButtonByText(socket, "返回"); // 修改代码+OpenAIConnectVisualQA：从 API Key 步骤点击真实返回按钮回到方法选择页；如果没有这行，后续 headless 流程找不到方法按钮。
  await waitForExpression(socket, "document.body.innerText.includes('选择 OpenAI 的登录方式')", "OpenAI method picker after API key step"); // 新增代码+OpenAIConnectVisualQA：等待返回方法选择页；如果没有这行，后续点击可能打到旧表单。
  await clickByTestId(socket, "provider-auth-method-chatgpt-headless"); // 新增代码+OpenAIConnectVisualQA：选择 headless 方法；如果没有这行，设备码等待页不会出现。
  await waitForExpression(socket, "document.body.innerText.includes('等待授权') || document.body.innerText.includes('正在启动授权') || document.body.innerText.includes('启动授权失败') || document.body.innerText.includes('授权失败')", "headless auth intermediate state"); // 新增代码+OpenAIConnectVisualQA：等待 headless 点击后的任一可见状态；如果没有这行，失败时不知道卡在启动中还是错误态。
  const headlessIntermediate = await evaluate(socket, `(() => ({ text: document.body.innerText.slice(0, 2000), htmlLeak: /refresh_token|access_token|id_token|secret_ref/i.test(document.documentElement.outerHTML), attemptId: document.querySelector('.provider-connect-auth-attempt')?.dataset.authAttemptId || '' }))()`); // 新增代码+OpenAIConnectVisualQA：读取 headless 中间状态文本；如果没有这行，系统化调试缺少真实 GUI 证据。
  qaResult.assertions.push({ label: "headless intermediate visible state", passed: true, details: headlessIntermediate }); // 新增代码+OpenAIConnectVisualQA：记录中间状态到结果 JSON；如果没有这行，失败结果缺少 DOM 事实。
  await capture(socket, "openai_headless_intermediate_1365x768.png"); // 新增代码+OpenAIConnectVisualQA：保存 headless 中间状态截图；如果没有这行，调试时看不到点击后的界面。
  await waitForExpression(socket, "document.body.innerText.includes('等待授权') && (document.querySelector('.provider-connect-code-row input')?.value || '').includes('MOCK-OPENAI')", "headless auth waiting page"); // 修改代码+OpenAIConnectVisualQA：等待 headless 设备码页并从 input.value 读取设备码；如果没有这行，等待页加载失败不会被发现。
  const headlessFacts = await evaluate(socket, `(() => ({ attemptId: document.querySelector('.provider-connect-auth-attempt')?.dataset.authAttemptId || '', hasLink: document.body.innerText.includes('访问此链接'), codeValue: document.querySelector('.provider-connect-code-row input')?.value || '', hasWaiting: document.body.innerText.includes('等待授权'), tokenLeak: /refresh_token|access_token|id_token|secret_ref/i.test(document.documentElement.outerHTML) }))()`); // 修改代码+OpenAIConnectVisualQA：读取 headless 等待页事实并使用 input.value 获取确认码；如果没有这行，确认码和泄露状态无法断言。
  qaResult.waitingVisible = headlessFacts.hasWaiting; // 新增代码+OpenAIConnectVisualQA：把等待页可见状态写入顶层结果；如果没有这行，Task 8 机器可读验收缺少 waitingVisible。
  assertQa(headlessFacts.attemptId.startsWith("auth_attempt_"), "headless waiting page exposes non-secret attempt id", headlessFacts); // 新增代码+OpenAIConnectVisualQA：断言 attempt id 可供 QA 完成 mock；如果没有这行，后续 complete 无法定位。
  assertQa(headlessFacts.hasLink && headlessFacts.codeValue.includes("MOCK-OPENAI") && headlessFacts.hasWaiting, "headless waiting page shows link code and waiting status", headlessFacts); // 修改代码+OpenAIConnectVisualQA：断言等待页核心元素可见；如果没有这行，空等待页也可能通过。
  assertQa(!headlessFacts.tokenLeak, "headless waiting page has no token or secret locator leak", headlessFacts); // 修改代码+OpenAIConnectVisualQA：断言等待页无 token 或密钥定位字段且结果标签不写危险字段名；如果没有这行，截图泄密或运行 JSON 字段名污染可能漏过。
  await capture(socket, "openai_headless_waiting_1365x768.png"); // 新增代码+OpenAIConnectVisualQA：保存 headless 等待页截图；如果没有这行，设备码 UI 没有视觉证据。
  const completed = await postBridge("/v2/gui/provider-settings/auth-attempt/complete", { attempt_id: headlessFacts.attemptId }); // 新增代码+OpenAIConnectVisualQA：通过 mock complete 模拟授权完成；如果没有这行，无法验证轮询完成后的 GUI 状态。
  assertQa(completed.attempt?.status === "complete", "mock complete returns complete status", completed); // 新增代码+OpenAIConnectVisualQA：断言后端完成状态；如果没有这行，complete 失败仍可能继续等。
  await waitForExpression(socket, "!document.querySelector('.provider-connect-dialog') && document.querySelector('[data-testid=\"provider-action-openai\"]')?.innerText.includes('断开')", "OpenAI mock connected row"); // 新增代码+OpenAIConnectVisualQA：等待轮询关闭弹窗并刷新已连接状态；如果没有这行，完成后的 GUI 不会被验证。
  await capture(socket, "openai_mock_connected_1365x768.png"); // 新增代码+OpenAIConnectVisualQA：保存 mock 已连接截图；如果没有这行，完成态没有视觉证据。
  const connectedLeakFacts = await evaluate(socket, `(() => ({ tokenLeak: /refresh_token|access_token|id_token|secret_ref/i.test(document.documentElement.outerHTML), mockVisible: document.body.innerText.includes('Mock ChatGPT auth') || document.body.innerText.includes('已连接') }))()`); // 新增代码+OpenAIConnectVisualQA：读取完成态泄露与连接事实；如果没有这行，完成后泄露无法发现。
  qaResult.rawSecretLeakFound = Boolean(pickerFacts.secretRefLeak || apiKeyFacts.tokenLeak || headlessIntermediate.htmlLeak || headlessFacts.tokenLeak || connectedLeakFacts.tokenLeak); // 新增代码+OpenAIConnectVisualQA：聚合运行时密钥泄露事实；如果没有这行，Task 8 JSON 无法直接证明没有 raw token 泄露。
  assertQa(!connectedLeakFacts.tokenLeak, "connected mock state has no token or secret locator leak", connectedLeakFacts); // 修改代码+OpenAIConnectVisualQA：断言完成态无 token 或密钥定位字段且结果标签不写危险字段名；如果没有这行，catalog 泄露或运行 JSON 字段名污染可能漏过。
  assertQa(connectedLeakFacts.mockVisible, "connected mock state is visible", connectedLeakFacts); // 新增代码+OpenAIConnectVisualQA：断言完成态可见；如果没有这行，用户可能看不到连接结果。
  await clickByTestId(socket, "provider-action-openai"); // 新增代码+OpenAIConnectVisualQA：断开 mock 连接以测试 browser flow；如果没有这行，重新连接入口不可用。
  await waitForExpression(socket, "document.querySelector('[data-testid=\"provider-action-openai\"]')?.innerText.includes('连接')", "OpenAI disconnected after mock"); // 新增代码+OpenAIConnectVisualQA：等待断开完成；如果没有这行，browser flow 会被已连接状态阻挡。
  await clickByTestId(socket, "provider-action-openai"); // 新增代码+OpenAIConnectVisualQA：再次打开 OpenAI 连接弹窗；如果没有这行，browser 方法无法选择。
  await waitForExpression(socket, "document.body.innerText.includes('选择 OpenAI 的登录方式')", "OpenAI method picker before browser"); // 新增代码+OpenAIConnectVisualQA：等待方法选择器重现；如果没有这行，后续按钮可能不存在。
  await clickByTestId(socket, "provider-auth-method-chatgpt-browser"); // 新增代码+OpenAIConnectVisualQA：选择 browser 方法；如果没有这行，浏览器授权等待页不会出现。
  await waitForExpression(socket, "document.body.innerText.includes('等待授权') && (document.querySelector('.provider-connect-code-row input')?.value || '').includes('Complete authorization')", "browser auth waiting page"); // 修改代码+OpenAIConnectVisualQA：等待 browser 授权提示页并从 input.value 读取提示语；如果没有这行，输入框里的提示语不会进入 innerText，driver 会误判真实 GUI 失败。
  const browserAttemptId = await evaluate(socket, "document.querySelector('.provider-connect-auth-attempt')?.dataset.authAttemptId || ''"); // 新增代码+OpenAIConnectVisualQA：读取 browser flow attempt id；如果没有这行，无法验证取消后状态。
  assertQa(String(browserAttemptId).startsWith("auth_attempt_"), "browser waiting page exposes non-secret attempt id", { browserAttemptId }); // 新增代码+OpenAIConnectVisualQA：断言 browser attempt id 存在；如果没有这行，取消状态无法追踪。
  await capture(socket, "openai_browser_waiting_1365x768.png"); // 新增代码+OpenAIConnectVisualQA：保存 browser 等待页截图；如果没有这行，browser flow 没有视觉证据。
  await evaluate(socket, "document.querySelector('.provider-connect-close')?.click()"); // 新增代码+OpenAIConnectVisualQA：点击连接弹窗关闭按钮；如果没有这行，取消路径不会触发。
  await waitForExpression(socket, "!document.querySelector('.provider-connect-dialog')", "connect dialog closed after cancel"); // 新增代码+OpenAIConnectVisualQA：等待弹窗关闭；如果没有这行，取消 UI 无法验证。
  await sleep(800); // 新增代码+OpenAIConnectVisualQA：等待前端异步 cancel 请求到达 bridge；如果没有这行，马上查 status 可能仍是 pending。
  const cancelled = await getBridge(`/v2/gui/provider-settings/auth-attempt/status?attempt_id=${encodeURIComponent(browserAttemptId)}`); // 新增代码+OpenAIConnectVisualQA：读取 browser attempt 取消后状态；如果没有这行，关闭按钮可能只关 UI 不取消后端。
  assertQa(cancelled.attempt?.status === "expired" && cancelled.attempt?.message === "cancelled_by_user", "browser cancel marks attempt expired", cancelled); // 新增代码+OpenAIConnectVisualQA：断言取消收敛为 expired；如果没有这行，pending 残留不会失败。
  await setViewport(socket, 390, 844); // 新增代码+OpenAIConnectVisualQA：切到移动宽度；如果没有这行，窄屏方法选择器没有证据。
  await clickByTestId(socket, "provider-action-openai"); // 新增代码+OpenAIConnectVisualQA：移动宽度下打开 OpenAI 连接弹窗；如果没有这行，移动截图没有对象。
  await waitForExpression(socket, "document.body.innerText.includes('选择 OpenAI 的登录方式')", "mobile method picker"); // 新增代码+OpenAIConnectVisualQA：等待移动方法选择器；如果没有这行，截图可能捕获旧布局。
  const mobileFacts = await evaluate(socket, `(() => ({ scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth, overflowOk: document.documentElement.scrollWidth <= window.innerWidth + 2, hasPicker: document.body.innerText.includes('选择 OpenAI 的登录方式') }))()`); // 新增代码+OpenAIConnectVisualQA：读取移动横向滚动事实；如果没有这行，窄屏溢出无法断言。
  assertQa(mobileFacts.overflowOk && mobileFacts.hasPicker, "mobile method picker has no horizontal overflow", mobileFacts); // 新增代码+OpenAIConnectVisualQA：断言移动方法选择器不横向溢出；如果没有这行，小屏重叠不会失败。
  await capture(socket, "openai_method_picker_mobile_390x844.png"); // 新增代码+OpenAIConnectVisualQA：保存移动方法选择截图；如果没有这行，移动验收没有视觉证据。
  qaResult.ok = true; // 修改代码+OpenAIConnectVisualQA：标记 QA 成功；如果没有这行，结果 JSON 不知道流程通过。
  socket.close(); // 修改代码+OpenAIConnectVisualQA：关闭 CDP 连接；如果没有这行，脚本退出前会残留连接。
} // 修改代码+OpenAIConnectVisualQA：函数段结束，run 到此结束；如果没有这行，函数语法不完整。

try { // 新增代码+ProviderSettingsVisualQA：主入口开始，捕获所有失败；如果没有这段，失败结果 JSON 不会写入。
  await run(); // 新增代码+ProviderSettingsVisualQA：执行视觉 QA 主流程；如果没有这行，脚本不会做任何事。
} catch (error) { // 新增代码+ProviderSettingsVisualQA：捕获主流程异常；如果没有这行，失败无法结构化记录。
  qaResult.ok = false; // 新增代码+ProviderSettingsVisualQA：标记 QA 失败；如果没有这行，失败结果可能误认为通过。
  qaResult.error = error instanceof Error ? error.message : String(error); // 新增代码+ProviderSettingsVisualQA：保存错误消息；如果没有这行，排查不知道失败原因。
  process.exitCode = 1; // 新增代码+ProviderSettingsVisualQA：设置失败退出码；如果没有这行，调用脚本会误判成功。
} finally { // 新增代码+ProviderSettingsVisualQA：最终写入证据；如果没有这段，成功或失败都缺少结果 JSON。
  await fs.mkdir(evidenceDir, { recursive: true }); // 新增代码+ProviderSettingsVisualQA：确保结果目录存在；如果没有这行，写 JSON 可能失败。
  await fs.writeFile(path.join(evidenceDir, "openai_connect_visual_qa_result.json"), JSON.stringify(qaResult, null, 2), "utf-8"); // 修改代码+OpenAIConnectVisualQA：写入 OpenAI connect 机器可读结果；如果没有这行，Task 8 证据不完整。
} // 新增代码+ProviderSettingsVisualQA：主入口结束；如果没有这行，try/catch/finally 语法不完整。
