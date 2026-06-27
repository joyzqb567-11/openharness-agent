export function urlOriginOrEmpty(rawUrl: string): string { // 新增代码+OAuthExternalBrowser：函数段开始，把任意 URL 转成 origin；如果没有这段，外链判断会在坏 URL 上抛异常。
  try { // 新增代码+OAuthExternalBrowser：尝试使用标准 URL 解析；如果没有这行，合法 URL 也无法提取 origin。
    return new URL(rawUrl).origin; // 新增代码+OAuthExternalBrowser：返回协议、域名和端口组成的 origin；如果没有这行，无法区分 Vite 页面和 OpenAI 授权页。
  } catch { // 新增代码+OAuthExternalBrowser：捕获非法 URL；如果没有这行，坏链接会让主进程崩溃。
    return ""; // 新增代码+OAuthExternalBrowser：非法 URL 返回空 origin；如果没有这行，调用方无法安全判断。
  } // 新增代码+OAuthExternalBrowser：异常处理结束；如果没有这行，TypeScript 语法不完整。
} // 新增代码+OAuthExternalBrowser：函数段结束，urlOriginOrEmpty 到此结束；如果没有边界说明，用户不容易看出它只做解析。

export function shouldOpenExternalDesktopUrl(rawUrl: string, rendererUrl: string | undefined): boolean { // 新增代码+OAuthExternalBrowser：函数段开始，判断链接是否应该交给系统浏览器；如果没有这段，OAuth 链接会继续开在 Electron 内部窗口。
  const targetOrigin = urlOriginOrEmpty(rawUrl); // 新增代码+OAuthExternalBrowser：解析目标 URL 的 origin；如果没有这行，后续无法比较是否是外部网站。
  if (targetOrigin.length === 0) { // 新增代码+OAuthExternalBrowser：非法或非标准 URL 不按外链处理；如果没有这行，坏 URL 可能触发外部打开。
    return false; // 新增代码+OAuthExternalBrowser：返回不外部打开；如果没有这行，主进程可能把不可识别链接交给系统。
  } // 新增代码+OAuthExternalBrowser：非法 URL 分支结束；如果没有这行，条件块语法不完整。
  const rendererOrigin = rendererUrl ? urlOriginOrEmpty(rendererUrl) : ""; // 新增代码+OAuthExternalBrowser：解析当前 renderer dev server origin；如果没有这行，开发模式会把自己也当外链。
  if (rendererOrigin.length > 0 && targetOrigin === rendererOrigin) { // 新增代码+OAuthExternalBrowser：识别 Vite 自己的页面；如果没有这行，开发页刷新可能被送去系统浏览器。
    return false; // 新增代码+OAuthExternalBrowser：renderer 自己不外部打开；如果没有这行，桌面壳会丢失主页面。
  } // 新增代码+OAuthExternalBrowser：renderer origin 分支结束；如果没有这行，条件块语法不完整。
  return rawUrl.startsWith("http://") || rawUrl.startsWith("https://"); // 新增代码+OAuthExternalBrowser：只有普通网页链接才交给系统浏览器；如果没有这行，file/about/devtools 等内部协议可能被错误外部打开。
} // 新增代码+OAuthExternalBrowser：函数段结束，shouldOpenExternalDesktopUrl 到此结束；如果没有边界说明，用户不容易看出它只做外链判断。
