import { describe, expect, it } from "vitest"; // 新增代码+DesktopBridgeConfigTest：引入 Vitest 测试工具；如果没有这行，preload bridge 配置无法自动验证。
import { createDesktopBridgeConfig } from "../src/preload/bridgeConfig"; // 新增代码+DesktopBridgeConfigTest：导入 preload 配置解析函数；如果没有这行，测试没有被测对象。

describe("createDesktopBridgeConfig", () => { // 新增代码+DesktopBridgeConfigTest：测试段开始，覆盖 Electron additionalArguments 到 bridge 配置的转换；如果没有这段，GUI 可能再次出现窗口打开但 bridge 未注入。
  it("returns decoded bridge config from Electron arguments", () => { // 新增代码+DesktopBridgeConfigTest：验证正常参数解析；如果没有这段，baseUrl/token 编码传递可能悄悄损坏。
    const config = createDesktopBridgeConfig([ // 新增代码+DesktopBridgeConfigTest：构造 Electron 参数数组；如果没有这行，测试没有输入。
      "--ignored=value", // 新增代码+DesktopBridgeConfigTest：放入无关参数；如果没有这行，无法证明解析逻辑不会误读相似参数。
      `--openharness-gui-bridge-url=${encodeURIComponent("http://127.0.0.1:8776")}`, // 新增代码+DesktopBridgeConfigTest：放入编码后的 bridge 地址；如果没有这行，无法验证 baseUrl 读取。
      `--openharness-gui-bridge-token=${encodeURIComponent("token with space")}`, // 新增代码+DesktopBridgeConfigTest：放入含空格的 token；如果没有这行，无法验证解码行为。
    ]); // 新增代码+DesktopBridgeConfigTest：参数数组结束；如果没有这行，数组语法不完整。

    expect(config).toEqual({ baseUrl: "http://127.0.0.1:8776", token: "token with space" }); // 新增代码+DesktopBridgeConfigTest：确认解析结果；如果没有这行，测试不会锁定 preload 注入合同。
  }); // 新增代码+DesktopBridgeConfigTest：正常参数测试结束；如果没有这行，测试块语法不完整。

  it("returns undefined when bridge config is incomplete", () => { // 新增代码+DesktopBridgeConfigTest：验证缺参时不注入半配置；如果没有这段，AppShell 可能拿到无效 token 后循环报错。
    expect(createDesktopBridgeConfig(["--openharness-gui-bridge-url=http%3A%2F%2F127.0.0.1%3A8776"])).toBeUndefined(); // 新增代码+DesktopBridgeConfigTest：只给地址时返回 undefined；如果没有这行，缺 token 仍会进入渲染层。
  }); // 新增代码+DesktopBridgeConfigTest：缺参测试结束；如果没有这行，测试块语法不完整。

  it("falls back to environment variables when Electron arguments are unavailable", () => { // 新增代码+DesktopBridgeConfigTest：验证环境变量兜底；如果没有这段，sandbox preload 拿不到 argv 时会再次断开 bridge。
    const config = createDesktopBridgeConfig([], { // 新增代码+DesktopBridgeConfigTest：构造没有 additionalArguments 的场景；如果没有这行，测试不能覆盖真实 Electron 失败路径。
      OPENHARNESS_GUI_BRIDGE_URL: "http://127.0.0.1:8776", // 新增代码+DesktopBridgeConfigTest：提供环境变量中的 bridge 地址；如果没有这行，兜底配置不完整。
      OPENHARNESS_GUI_BRIDGE_TOKEN: "env-token", // 新增代码+DesktopBridgeConfigTest：提供环境变量中的 token；如果没有这行，兜底配置不完整。
    }); // 新增代码+DesktopBridgeConfigTest：环境变量对象结束；如果没有这行，对象语法不完整。

    expect(config).toEqual({ baseUrl: "http://127.0.0.1:8776", token: "env-token" }); // 新增代码+DesktopBridgeConfigTest：确认环境变量兜底结果；如果没有这行，测试不会锁住 sandbox 场景修复。
  }); // 新增代码+DesktopBridgeConfigTest：环境变量兜底测试结束；如果没有这行，测试块语法不完整。
}); // 新增代码+DesktopBridgeConfigTest：测试段结束；如果没有这行，describe 语法不完整。
