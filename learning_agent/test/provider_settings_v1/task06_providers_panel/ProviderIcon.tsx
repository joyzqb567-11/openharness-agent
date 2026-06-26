type ProviderIconProps = { // 新增代码+ProviderSettingsPanel：类型段开始，定义 provider 图标输入；如果没有这段，Provider 行无法稳定传入 id 和名称。
  providerId: string; // 新增代码+ProviderSettingsPanel：保存 provider id；如果没有这行，图标无法按提供商生成稳定缩写。
  displayName: string; // 新增代码+ProviderSettingsPanel：保存 provider 名称；如果没有这行，自定义 provider 无法生成兜底缩写。
}; // 新增代码+ProviderSettingsPanel：ProviderIconProps 类型结束；如果没有这行，TypeScript 类型语法不完整。

function providerInitials(providerId: string, displayName: string): string { // 新增代码+ProviderSettingsPanel：函数段开始，生成 provider 图标缩写；如果没有这段，列表左侧图标只能硬编码。
  if (providerId === "github-copilot") { // 新增代码+ProviderSettingsPanel：识别 GitHub Copilot；如果没有这行，Copilot 缩写会不稳定。
    return "GH"; // 新增代码+ProviderSettingsPanel：返回 GitHub 缩写；如果没有这行，Copilot 行没有清楚标识。
  } // 新增代码+ProviderSettingsPanel：Copilot 分支结束；如果没有这行，条件块语法不完整。
  if (providerId === "openrouter") { // 新增代码+ProviderSettingsPanel：识别 OpenRouter；如果没有这行，OpenRouter 缩写会退成单字母。
    return "OR"; // 新增代码+ProviderSettingsPanel：返回 OpenRouter 缩写；如果没有这行，OpenRouter 行不易扫描。
  } // 新增代码+ProviderSettingsPanel：OpenRouter 分支结束；如果没有这行，条件块语法不完整。
  if (providerId === "vercel") { // 新增代码+ProviderSettingsPanel：识别 Vercel AI Gateway；如果没有这行，Vercel 缩写会不稳定。
    return "VA"; // 新增代码+ProviderSettingsPanel：返回 Vercel AI 缩写；如果没有这行，Vercel 行不易扫描。
  } // 新增代码+ProviderSettingsPanel：Vercel 分支结束；如果没有这行，条件块语法不完整。
  const words = displayName.trim().split(/\s+/).filter(Boolean); // 新增代码+ProviderSettingsPanel：按空格切分显示名；如果没有这行，自定义 provider 无法生成缩写。
  const initials = words.slice(0, 2).map((word) => word.slice(0, 1).toUpperCase()).join(""); // 新增代码+ProviderSettingsPanel：取前两个词首字母；如果没有这行，图标文本会过长。
  return initials.length > 0 ? initials : providerId.slice(0, 2).toUpperCase(); // 新增代码+ProviderSettingsPanel：返回缩写或 id 兜底；如果没有这行，空名称 provider 会没有图标文本。
} // 新增代码+ProviderSettingsPanel：函数段结束，providerInitials 到此结束；如果没有这行，函数语法不完整。

export function ProviderIcon({ providerId, displayName }: ProviderIconProps): JSX.Element { // 新增代码+ProviderSettingsPanel：函数段开始，渲染 provider 左侧图标；如果没有这段，Provider 行缺少视觉锚点。
  return <span className={`provider-icon provider-icon-${providerId.replace(/[^a-z0-9-]/g, "-")}`} aria-hidden={true}>{providerInitials(providerId, displayName)}</span>; // 新增代码+ProviderSettingsPanel：输出圆形缩写图标；如果没有这行，列表左侧没有可扫描标识。
} // 新增代码+ProviderSettingsPanel：函数段结束，ProviderIcon 到此结束；如果没有这个边界，用户不容易看出图标组件范围。
