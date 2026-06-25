import { describe, expect, it } from "vitest"; // 新增代码+DesktopSettingsStoreTest：导入 Vitest 测试工具；如果没有这行，settingsStore 合同无法自动验证。
import { bridgeDisplayFromUrl, buildSettingsViewModel, diagnosticBundleCopyText, diagnosticsStatusLabel, featureFlagRows } from "../src/state/settingsStore"; // 新增代码+DesktopSettingsStoreTest：导入设置纯函数；如果没有这行，测试没有被测目标。

describe("settingsStore", () => { // 新增代码+DesktopSettingsStoreTest：测试段开始，覆盖设置和诊断 view model；如果没有这段测试，设置页安全行为容易回退。
  it("shows bridge host and port without token material", () => { // 新增代码+DesktopSettingsStoreTest：验证 bridge URL 脱敏；如果没有这段测试，token query/hash 可能进入设置页。
    const display = bridgeDisplayFromUrl("http://127.0.0.1:8776/api?token=abc123#openharnessBridgeToken=secret"); // 新增代码+DesktopSettingsStoreTest：构造带 token 的 URL；如果没有这行，脱敏场景不真实。
    expect(display.host).toBe("127.0.0.1"); // 新增代码+DesktopSettingsStoreTest：确认 host 保留；如果没有这行，连接目标可能显示错误。
    expect(display.port).toBe("8776"); // 新增代码+DesktopSettingsStoreTest：确认 port 保留；如果没有这行，用户无法确认 bridge 端口。
    expect(display.origin).toBe("http://127.0.0.1:8776"); // 新增代码+DesktopSettingsStoreTest：确认 origin 不含路径、query、hash；如果没有这行，token 可能泄露。
    expect(JSON.stringify(display)).not.toContain("abc123"); // 新增代码+DesktopSettingsStoreTest：确认 query token 不出现；如果没有这行，安全回归会漏过。
    expect(JSON.stringify(display)).not.toContain("secret"); // 新增代码+DesktopSettingsStoreTest：确认 hash token 不出现；如果没有这行，桌面注入 token 可能被显示。
  }); // 新增代码+DesktopSettingsStoreTest：bridge URL 测试结束；如果没有这行，测试块语法不完整。

  it("sorts feature flags and renders readable labels", () => { // 新增代码+DesktopSettingsStoreTest：验证 feature flags 规范化；如果没有这段测试，设置页开关顺序和文案会漂移。
    const rows = featureFlagRows({ streaming: true, diagnostics: false }); // 新增代码+DesktopSettingsStoreTest：构造无序开关对象；如果没有这行，排序逻辑没有输入。
    expect(rows).toEqual([{ name: "diagnostics", enabled: false, label: "已关闭" }, { name: "streaming", enabled: true, label: "已启用" }]); // 新增代码+DesktopSettingsStoreTest：确认排序和中文标签；如果没有这行，UI 可读性可能回退。
  }); // 新增代码+DesktopSettingsStoreTest：feature flags 测试结束；如果没有这行，测试块语法不完整。

  it("builds a settings view model from health and diagnostics payloads", () => { // 新增代码+DesktopSettingsStoreTest：验证设置 view model 合成；如果没有这段测试，SettingsPanel 会直接依赖原始 payload。
    const model = buildSettingsViewModel({ bridgeBaseUrl: "http://localhost:9001/#token=hidden", themeChoice: "浅色", health: { model_provider: { provider: "OpenAI", model: "gpt-5" }, feature_flags: { settings: true } }, diagnostics: { diagnostic_bundle: { log_path: "memory/gui_bridge", evidence_path: "learning_agent/test/desktop_gui_shell_v2" } } }); // 新增代码+DesktopSettingsStoreTest：构造 health/diagnostics 输入；如果没有这行，view model 没有真实字段来源。
    expect(model.provider).toBe("OpenAI"); // 新增代码+DesktopSettingsStoreTest：确认 provider 透传；如果没有这行，设置页可能显示兜底而非事实。
    expect(model.model).toBe("gpt-5"); // 新增代码+DesktopSettingsStoreTest：确认 model 透传；如果没有这行，模型名可能丢失。
    expect(model.bridge.port).toBe("9001"); // 新增代码+DesktopSettingsStoreTest：确认 bridge 端口；如果没有这行，连接信息可能错误。
    expect(model.themeChoice).toBe("浅色"); // 新增代码+DesktopSettingsStoreTest：确认主题选择；如果没有这行，设置项可能不更新。
    expect(model.featureFlags).toHaveLength(1); // 新增代码+DesktopSettingsStoreTest：确认功能开关进入 view model；如果没有这行，能力列表可能为空。
    expect(model.logPath).toBe("memory/gui_bridge"); // 新增代码+DesktopSettingsStoreTest：确认日志目录；如果没有这行，用户找不到诊断文件。
  }); // 新增代码+DesktopSettingsStoreTest：view model 测试结束；如果没有这行，测试块语法不完整。

  it("reads diagnostic copy text and degraded labels safely", () => { // 新增代码+DesktopSettingsStoreTest：验证诊断复制文本和状态标签；如果没有这段测试，诊断按钮可能复制空内容。
    const diagnostics = { ok: true, status_degraded: true, diagnostic_bundle: { copy_text: "{\"redacted\":true}" } }; // 新增代码+DesktopSettingsStoreTest：构造降级诊断 payload；如果没有这行，状态判断没有输入。
    expect(diagnosticBundleCopyText(diagnostics)).toBe("{\"redacted\":true}"); // 新增代码+DesktopSettingsStoreTest：确认复制文本读取；如果没有这行，复制按钮可能拿错字段。
    expect(diagnosticsStatusLabel(diagnostics)).toBe("已降级"); // 新增代码+DesktopSettingsStoreTest：确认降级标签；如果没有这行，snapshot 失败可能显示正常。
    expect(diagnosticsStatusLabel({ ok: false })).toBe("后端离线"); // 新增代码+DesktopSettingsStoreTest：确认离线标签；如果没有这行，离线状态可能误导用户。
  }); // 新增代码+DesktopSettingsStoreTest：诊断文本测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopSettingsStoreTest：测试段结束；如果没有这行，describe 语法不完整。
