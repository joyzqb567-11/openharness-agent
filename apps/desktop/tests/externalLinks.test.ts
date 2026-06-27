import { describe, expect, it } from "vitest"; // 新增代码+OAuthExternalBrowserTest：导入 Vitest 测试 API；如果没有这行，外链规则没有自动化断言。
import { shouldOpenExternalDesktopUrl, urlOriginOrEmpty } from "../src/main/externalLinks"; // 新增代码+OAuthExternalBrowserTest：导入纯函数；如果没有这行，测试无法覆盖 Electron 主进程外链判断。

describe("external desktop links", () => { // 新增代码+OAuthExternalBrowserTest：测试组开始，覆盖桌面外链策略；如果没有这段，OAuth 外链回归不容易被发现。
  it("opens OpenAI OAuth URLs in the system browser", () => { // 新增代码+OAuthExternalBrowserTest：测试 OpenAI OAuth 外链；如果没有这段，链接可能再次开进 Electron 内部窗口。
    expect(shouldOpenExternalDesktopUrl("https://auth.openai.com/oauth/authorize?client_id=test", "http://127.0.0.1:5177")).toBe(true); // 新增代码+OAuthExternalBrowserTest：断言 OpenAI 授权页必须外部打开；如果没有这行，真实 OAuth 可能无法复用系统浏览器登录态。
  }); // 新增代码+OAuthExternalBrowserTest：OpenAI OAuth 测试结束；如果没有这行，测试语法不完整。

  it("keeps the renderer dev origin inside Electron", () => { // 新增代码+OAuthExternalBrowserTest：测试 Vite renderer 不被外部打开；如果没有这段，开发模式主窗口可能被拦截。
    expect(shouldOpenExternalDesktopUrl("http://127.0.0.1:5177/#abc", "http://127.0.0.1:5177")).toBe(false); // 新增代码+OAuthExternalBrowserTest：断言同 origin renderer 留在 Electron；如果没有这行，桌面壳会无法加载。
  }); // 新增代码+OAuthExternalBrowserTest：renderer origin 测试结束；如果没有这行，测试语法不完整。

  it("ignores malformed URLs instead of crashing", () => { // 新增代码+OAuthExternalBrowserTest：测试坏 URL 安全路径；如果没有这段，坏链接可能让主进程异常。
    expect(urlOriginOrEmpty("not a valid url")).toBe(""); // 新增代码+OAuthExternalBrowserTest：断言坏 URL 解析为空；如果没有这行，helper 的容错没有证据。
    expect(shouldOpenExternalDesktopUrl("not a valid url", "http://127.0.0.1:5177")).toBe(false); // 新增代码+OAuthExternalBrowserTest：断言坏 URL 不外部打开；如果没有这行，系统可能收到不可识别链接。
  }); // 新增代码+OAuthExternalBrowserTest：坏 URL 测试结束；如果没有这行，测试语法不完整。
}); // 新增代码+OAuthExternalBrowserTest：测试组结束；如果没有这行，describe 语法不完整。
