# Stage 5 学习备份：Chrome 插件 MVP 只读能力计划

这是 `docs/superpowers/plans/2026-06-01-browser-dual-track-stage5-chrome-extension-readonly.md` 的学习备份。

本阶段只做 Chrome 插件路线的只读基础设施：extension 文件、native host 文件、只读消息协议、连接状态和 `ChromeExtensionProvider`。

本阶段不实现点击、输入、按键、提交、上传，也不安装真实插件到用户浏览器。

最终必须通过自动化测试、全量回归、真实可见终端验收和独立 verifier。

