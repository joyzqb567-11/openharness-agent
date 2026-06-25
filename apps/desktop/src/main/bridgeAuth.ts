import crypto from "node:crypto"; // 新增代码+DesktopBridgeAuth：使用 Node 加密随机数生成 bridge token；如果没有这行，桌面壳无法生成难猜的本地访问令牌。

export type BridgeAuth = { // 新增代码+DesktopBridgeAuth：定义主进程传给桥接层的认证结构；如果没有这段，token 和 header 的形状不清楚。
  token: string; // 新增代码+DesktopBridgeAuth：保存原始 token；如果没有这行，主进程无法把 token 交给后端 bridge。
  headers: Record<string, string>; // 新增代码+DesktopBridgeAuth：保存前端请求需要的 header；如果没有这行，渲染进程无法复用统一请求头。
}; // 新增代码+DesktopBridgeAuth：BridgeAuth 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function createBridgeAuth(): BridgeAuth { // 新增代码+DesktopBridgeAuth：函数段开始，用于生成一次性桌面 bridge 认证信息；如果没有这段，GUI bridge 会缺少本地安全边界。
  const token = crypto.randomBytes(32).toString("hex"); // 新增代码+DesktopBridgeAuth：生成 32 字节随机 token；如果没有这行，bridge token 可能固定或太容易猜。
  return { // 新增代码+DesktopBridgeAuth：返回 token 与请求头；如果没有这行，调用方拿不到认证数据。
    token, // 新增代码+DesktopBridgeAuth：返回原始 token 供主进程启动后端时使用；如果没有这行，后端无法知道应接受哪个 token。
    headers: { // 新增代码+DesktopBridgeAuth：封装 HTTP header；如果没有这段，前端每次请求都要手写安全 header。
      "X-OpenHarness-Desktop-Token": token, // 新增代码+DesktopBridgeAuth：使用蓝图约定的 token header；如果没有这行，后端安全测试会拒绝请求。
    }, // 新增代码+DesktopBridgeAuth：headers 对象结束；如果没有这行，返回结构语法不完整。
  }; // 新增代码+DesktopBridgeAuth：认证结构返回结束；如果没有这行，函数没有返回值。
} // 新增代码+DesktopBridgeAuth：函数段结束，createBridgeAuth 到此结束；如果没有这段边界，用户不容易看出 token 生成逻辑范围。
