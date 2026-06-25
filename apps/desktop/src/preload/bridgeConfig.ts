export type DesktopBridgeConfig = { // 新增代码+DesktopBridgeConfig：定义 preload 注入给渲染层的 bridge 配置形状；如果没有这段，React 无法用类型确认 baseUrl 和 token 是否存在。
  baseUrl: string; // 新增代码+DesktopBridgeConfig：保存 GUI bridge 的本地地址；如果没有这行，渲染层不知道应该请求哪个后端端口。
  token: string; // 新增代码+DesktopBridgeConfig：保存 GUI bridge 的访问令牌；如果没有这行，后端安全端点会拒绝渲染层请求。
}; // 新增代码+DesktopBridgeConfig：bridge 配置类型结束；如果没有这行，TypeScript 类型声明不完整。
type DesktopBridgeEnvironment = Record<string, string | undefined>; // 新增代码+DesktopBridgeConfig：定义 preload 可读取的环境变量形状；如果没有这行，process.env 兜底会变成不清楚的任意对象。

function readAdditionalArgument(args: readonly string[], name: string): string { // 新增代码+DesktopBridgeConfig：函数段开始，从 Electron additionalArguments 读取指定参数；如果没有这段，preload 无法拿到主进程传来的 bridge 配置。
  const prefix = `--${name}=`; // 新增代码+DesktopBridgeConfig：构造命令行参数前缀；如果没有这行，查找参数时会把其它相似参数误认成目标。
  const rawValue = args.find((arg) => arg.startsWith(prefix))?.slice(prefix.length) ?? ""; // 新增代码+DesktopBridgeConfig：找到参数并截取值；如果没有这行，preload 永远读不到 baseUrl/token。
  return rawValue ? decodeURIComponent(rawValue) : ""; // 新增代码+DesktopBridgeConfig：解码主进程编码后的值；如果没有这行，URL 或 token 中的特殊字符可能无法还原。
} // 新增代码+DesktopBridgeConfig：函数段结束，readAdditionalArgument 到此结束；如果没有这段边界，用户不容易看出它只负责读单个参数。

function readEnvironmentValue(env: DesktopBridgeEnvironment, name: string): string { // 新增代码+DesktopBridgeConfig：函数段开始，从环境变量读取 bridge 配置兜底；如果没有这段，sandbox preload 拿不到 additionalArguments 时就会断开。
  return env[name] ?? ""; // 新增代码+DesktopBridgeConfig：返回环境变量值或空字符串；如果没有这行，缺失变量会把 undefined 泄漏到配置判断里。
} // 新增代码+DesktopBridgeConfig：函数段结束，readEnvironmentValue 到此结束；如果没有这段边界，用户不容易看出它只负责环境变量兜底。

export function createDesktopBridgeConfig(args: readonly string[], env: DesktopBridgeEnvironment = {}): DesktopBridgeConfig | undefined { // 新增代码+DesktopBridgeConfig：函数段开始，把 Electron 参数或环境变量转成渲染层可用配置；如果没有这段，AppShell 会一直提示 bridge 未注入。
  const baseUrl = readAdditionalArgument(args, "openharness-gui-bridge-url") || readEnvironmentValue(env, "OPENHARNESS_GUI_BRIDGE_URL"); // 修改代码+DesktopBridgeConfig：优先读取 additionalArguments，失败时读取环境变量；如果没有这行，Electron sandbox 场景会丢失 baseUrl。
  const token = readAdditionalArgument(args, "openharness-gui-bridge-token") || readEnvironmentValue(env, "OPENHARNESS_GUI_BRIDGE_TOKEN"); // 修改代码+DesktopBridgeConfig：优先读取 additionalArguments，失败时读取环境变量 token；如果没有这行，GUI 请求会缺少认证令牌。
  if (!baseUrl || !token) { // 新增代码+DesktopBridgeConfig：检查配置是否完整；如果没有这行，缺失 token 的半配置会进入渲染层并造成循环失败。
    return undefined; // 新增代码+DesktopBridgeConfig：配置不完整时不注入 bridge；如果没有这行，UI 无法区分“没配置”和“配置坏了”。
  } // 新增代码+DesktopBridgeConfig：配置完整性判断结束；如果没有这行，条件块语法不完整。
  return { baseUrl, token }; // 新增代码+DesktopBridgeConfig：返回可注入的 bridge 配置；如果没有这行，AppShell 拿不到后端连接信息。
} // 新增代码+DesktopBridgeConfig：函数段结束，createDesktopBridgeConfig 到此结束；如果没有这段边界，用户不容易看出它负责 bridge 配置组装。
