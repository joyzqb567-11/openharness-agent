export type FeatureFlagRow = { // 新增代码+DesktopSettingsStore：类型段开始，描述设置页功能开关行；如果没有这段类型，组件会直接使用松散对象。
  name: string; // 新增代码+DesktopSettingsStore：保存功能开关名称；如果没有这行，设置页不知道每个开关叫什么。
  enabled: boolean; // 新增代码+DesktopSettingsStore：保存功能开关是否启用；如果没有这行，设置页无法显示启用/关闭状态。
  label: string; // 新增代码+DesktopSettingsStore：保存可读中文状态；如果没有这行，组件要重复把布尔值转成人话。
}; // 新增代码+DesktopSettingsStore：功能开关行类型结束；如果没有这行，TypeScript 类型语法不完整。

export type BridgeDisplay = { // 新增代码+DesktopSettingsStore：类型段开始，描述脱敏后的 bridge 地址；如果没有这段类型，设置页可能误显示 token。
  host: string; // 新增代码+DesktopSettingsStore：保存主机名；如果没有这行，用户无法确认连接目标。
  port: string; // 新增代码+DesktopSettingsStore：保存端口号；如果没有这行，用户无法确认 bridge 端口。
  origin: string; // 新增代码+DesktopSettingsStore：保存不含 token 的 origin；如果没有这行，复制或显示 URL 时可能带出 hash/query。
}; // 新增代码+DesktopSettingsStore：bridge 地址类型结束；如果没有这行，TypeScript 类型语法不完整。

export type SettingsViewModel = { // 新增代码+DesktopSettingsStore：类型段开始，描述设置面板要渲染的数据；如果没有这段类型，组件会直接依赖后端原始 payload。
  provider: string; // 新增代码+DesktopSettingsStore：保存 provider 名；如果没有这行，设置页无法显示模型来源。
  model: string; // 新增代码+DesktopSettingsStore：保存 model 名；如果没有这行，设置页无法显示当前模型。
  bridge: BridgeDisplay; // 新增代码+DesktopSettingsStore：保存脱敏 bridge 地址；如果没有这行，设置页可能泄露 token。
  themeChoice: string; // 新增代码+DesktopSettingsStore：保存主题选择；如果没有这行，设置页无法显示视觉偏好。
  featureFlags: FeatureFlagRow[]; // 新增代码+DesktopSettingsStore：保存功能开关列表；如果没有这行，设置页没有能力概览。
  logPath: string; // 新增代码+DesktopSettingsStore：保存日志目录；如果没有这行，用户不知道从哪里找 bridge 日志。
  evidencePath: string; // 新增代码+DesktopSettingsStore：保存证据目录；如果没有这行，用户不知道验收资料放在哪里。
}; // 新增代码+DesktopSettingsStore：设置 view model 类型结束；如果没有这行，TypeScript 类型语法不完整。

function isRecord(value: unknown): value is Record<string, unknown> { // 新增代码+DesktopSettingsStore：函数段开始，判断未知值是否为对象；如果没有这段函数，字段读取会信任任意 JSON。
  return typeof value === "object" && value !== null && !Array.isArray(value); // 新增代码+DesktopSettingsStore：只接受普通对象；如果没有这行，数组或 null 会导致字段读取异常。
} // 新增代码+DesktopSettingsStore：函数段结束，isRecord 到此结束；如果没有这个边界，初学者不容易看出类型保护范围。

function textFrom(value: unknown, fallback: string): string { // 新增代码+DesktopSettingsStore：函数段开始，安全读取字符串；如果没有这段函数，undefined 会直接显示到 UI。
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : fallback; // 新增代码+DesktopSettingsStore：返回非空字符串或兜底；如果没有这行，设置页会出现空白关键字段。
} // 新增代码+DesktopSettingsStore：函数段结束，textFrom 到此结束；如果没有这个边界，初学者不容易看出字符串兜底范围。

export function bridgeDisplayFromUrl(baseUrl: string): BridgeDisplay { // 新增代码+DesktopSettingsStore：函数段开始，从 bridge URL 生成安全展示对象；如果没有这段函数，设置页可能显示 token query/hash。
  try { // 新增代码+DesktopSettingsStore：保护 URL 解析；如果没有这行，坏配置会让设置页崩溃。
    const parsed = new URL(baseUrl); // 新增代码+DesktopSettingsStore：使用浏览器 URL API 解析；如果没有这行，手写切割容易误留 token。
    return { host: parsed.hostname || "127.0.0.1", port: parsed.port || (parsed.protocol === "https:" ? "443" : "80"), origin: parsed.origin }; // 新增代码+DesktopSettingsStore：只返回 origin/host/port；如果没有这行，hash 或 query 中的 token 可能进入 UI。
  } catch { // 新增代码+DesktopSettingsStore：处理无效 URL；如果没有这行，坏 baseUrl 会抛异常。
    return { host: "未配置", port: "-", origin: "未配置" }; // 新增代码+DesktopSettingsStore：返回安全兜底；如果没有这行，设置页会空白或崩溃。
  } // 新增代码+DesktopSettingsStore：异常分支结束；如果没有这行，try/catch 语法不完整。
} // 新增代码+DesktopSettingsStore：函数段结束，bridgeDisplayFromUrl 到此结束；如果没有这个边界，初学者不容易看出 URL 脱敏范围。

export function featureFlagRows(flags: unknown): FeatureFlagRow[] { // 新增代码+DesktopSettingsStore：函数段开始，规范化 feature flags；如果没有这段函数，组件要直接遍历未知 JSON。
  const record = isRecord(flags) ? flags : {}; // 新增代码+DesktopSettingsStore：只接受对象型 flags；如果没有这行，数组或 null 会破坏渲染。
  return Object.entries(record).sort(([left], [right]) => left.localeCompare(right)).map(([name, enabled]) => ({ name, enabled: Boolean(enabled), label: Boolean(enabled) ? "已启用" : "已关闭" })); // 新增代码+DesktopSettingsStore：排序并转成人话；如果没有这行，开关列表顺序和文案不稳定。
} // 新增代码+DesktopSettingsStore：函数段结束，featureFlagRows 到此结束；如果没有这个边界，初学者不容易看出 flags 规范化范围。

export function diagnosticBundleCopyText(diagnostics: unknown): string { // 新增代码+DesktopSettingsStore：函数段开始，读取诊断复制文本；如果没有这段函数，复制按钮要理解后端嵌套结构。
  const diagnosticsRecord = isRecord(diagnostics) ? diagnostics : {}; // 新增代码+DesktopSettingsStore：保护诊断 payload；如果没有这行，坏 payload 会导致字段读取异常。
  const bundle = isRecord(diagnosticsRecord.diagnostic_bundle) ? diagnosticsRecord.diagnostic_bundle : {}; // 新增代码+DesktopSettingsStore：读取 diagnostic_bundle；如果没有这行，复制按钮可能访问 undefined。
  return textFrom(bundle.copy_text, "诊断包暂不可用"); // 新增代码+DesktopSettingsStore：返回复制文本或兜底；如果没有这行，点击复制可能写入空字符串。
} // 新增代码+DesktopSettingsStore：函数段结束，diagnosticBundleCopyText 到此结束；如果没有这个边界，初学者不容易看出复制文本来源。

export function diagnosticsStatusLabel(diagnostics: unknown): string { // 新增代码+DesktopSettingsStore：函数段开始，生成诊断状态标签；如果没有这段函数，诊断面板会重复判断 degraded/offline。
  const diagnosticsRecord = isRecord(diagnostics) ? diagnostics : {}; // 新增代码+DesktopSettingsStore：保护诊断 payload；如果没有这行，坏 payload 会导致字段读取异常。
  if (diagnosticsRecord.backend_online === false || diagnosticsRecord.ok === false) { // 新增代码+DesktopSettingsStore：优先识别离线；如果没有这行，离线会被误报成正常。
    return "后端离线"; // 新增代码+DesktopSettingsStore：返回离线文案；如果没有这行，用户不知道 bridge 不在线。
  } // 新增代码+DesktopSettingsStore：离线分支结束；如果没有这行，条件块语法不完整。
  if (diagnosticsRecord.status_degraded === true) { // 新增代码+DesktopSettingsStore：识别降级状态；如果没有这行，snapshot 失败不会被显眼展示。
    return "已降级"; // 新增代码+DesktopSettingsStore：返回降级文案；如果没有这行，用户无法区分部分可用。
  } // 新增代码+DesktopSettingsStore：降级分支结束；如果没有这行，条件块语法不完整。
  return "正常"; // 新增代码+DesktopSettingsStore：返回正常文案；如果没有这行，成功状态没有稳定标签。
} // 新增代码+DesktopSettingsStore：函数段结束，diagnosticsStatusLabel 到此结束；如果没有这个边界，初学者不容易看出状态判断范围。

export function buildSettingsViewModel(input: { bridgeBaseUrl?: string; health?: unknown; diagnostics?: unknown; themeChoice?: string }): SettingsViewModel { // 新增代码+DesktopSettingsStore：函数段开始，合成设置页 view model；如果没有这段函数，SettingsPanel 会直接揉多个后端 payload。
  const health = isRecord(input.health) ? input.health : {}; // 新增代码+DesktopSettingsStore：保护 health payload；如果没有这行，设置页会信任未知 JSON。
  const diagnostics = isRecord(input.diagnostics) ? input.diagnostics : {}; // 新增代码+DesktopSettingsStore：保护 diagnostics payload；如果没有这行，目录字段读取可能崩溃。
  const modelProvider = isRecord(health.model_provider) ? health.model_provider : {}; // 新增代码+DesktopSettingsStore：读取模型来源对象；如果没有这行，provider/model 字段会直接访问未知值。
  const bundle = isRecord(diagnostics.diagnostic_bundle) ? diagnostics.diagnostic_bundle : {}; // 新增代码+DesktopSettingsStore：读取诊断包对象；如果没有这行，日志目录和证据目录无法稳定兜底。
  return { // 新增代码+DesktopSettingsStore：返回设置 view model；如果没有这行，组件拿不到统一数据。
    provider: textFrom(modelProvider.provider, "OpenHarness"), // 新增代码+DesktopSettingsStore：设置 provider 文案；如果没有这行，设置页模型来源会空白。
    model: textFrom(modelProvider.model, "desktop-gui-bridge"), // 新增代码+DesktopSettingsStore：设置 model 文案；如果没有这行，设置页模型名会空白。
    bridge: bridgeDisplayFromUrl(input.bridgeBaseUrl ?? ""), // 新增代码+DesktopSettingsStore：生成脱敏 bridge 展示；如果没有这行，bridge URL 可能带 token。
    themeChoice: textFrom(input.themeChoice, "跟随系统"), // 新增代码+DesktopSettingsStore：设置主题选择；如果没有这行，主题栏没有稳定默认值。
    featureFlags: featureFlagRows(health.feature_flags), // 新增代码+DesktopSettingsStore：规范化功能开关；如果没有这行，设置页缺少能力概览。
    logPath: textFrom(bundle.log_path, "memory/gui_bridge"), // 新增代码+DesktopSettingsStore：设置日志目录；如果没有这行，用户不知道日志位置。
    evidencePath: textFrom(bundle.evidence_path, "learning_agent/test/desktop_gui_shell_v2"), // 新增代码+DesktopSettingsStore：设置证据目录；如果没有这行，用户不知道验收材料位置。
  }; // 新增代码+DesktopSettingsStore：设置 view model 结束；如果没有这行，对象语法不完整。
} // 新增代码+DesktopSettingsStore：函数段结束，buildSettingsViewModel 到此结束；如果没有这个边界，初学者不容易看出设置数据合成范围。
