import { defineConfig } from "vite"; // 新增代码+DesktopBootstrap：引入 Vite 配置函数；如果没有这行，渲染进程没有统一的构建入口。
import react from "@vitejs/plugin-react"; // 新增代码+DesktopBootstrap：启用 React JSX 转换；如果没有这行，TSX 组件无法被 Vite 正确编译。

export default defineConfig({ // 新增代码+DesktopBootstrap：导出桌面渲染进程配置；如果没有这段，npm run build:renderer 不知道如何打包页面。
  plugins: [react()], // 新增代码+DesktopBootstrap：注册 React 插件；如果没有这行，React 快刷新和 JSX 编译都会缺失。
  root: ".", // 新增代码+DesktopBootstrap：把 apps/desktop 作为前端根目录；如果没有这行，Vite 可能从错误位置找 index.html。
  server: { // 新增代码+DesktopBootstrap：声明开发服务器配置；如果没有这段，Electron 开发模式无法稳定连接渲染页。
    host: "127.0.0.1", // 新增代码+DesktopBootstrap：只监听本机回环地址；如果没有这行，开发服务可能暴露到局域网。
    port: 5177, // 新增代码+DesktopBootstrap：固定渲染开发端口；如果没有这行，主进程难以找到前端页面。
  }, // 新增代码+DesktopBootstrap：开发服务器配置结束；如果没有这行，配置对象语法不完整。
  build: { // 新增代码+DesktopBootstrap：声明生产构建位置；如果没有这段，Electron 无法从 dist 加载静态页面。
    outDir: "dist/renderer", // 新增代码+DesktopBootstrap：把渲染产物放到 dist/renderer；如果没有这行，主进程加载路径会找不到页面。
    emptyOutDir: true, // 新增代码+DesktopBootstrap：构建前清理旧渲染产物；如果没有这行，旧文件可能混入新版本。
  }, // 新增代码+DesktopBootstrap：生产构建配置结束；如果没有这行，配置对象语法不完整。
}); // 新增代码+DesktopBootstrap：Vite 配置结束；如果没有这行，TypeScript 语法不完整。
