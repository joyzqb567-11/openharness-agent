// 新增代码+ChromeExtensionStage5: 定位输出区域；若没有这行代码，options 页面无法显示调试结果。
const output = document.getElementById("output");

// 新增代码+ChromeExtensionStage5: 定位 tabs context 按钮；若没有这行代码，用户无法从 options 页面触发只读检查。
const button = document.getElementById("tabs-context");

// 新增代码+ChromeExtensionStage5: 绑定按钮点击事件；若没有这行代码，options 页面只是静态文本。
button.addEventListener("click", () => {
  // 新增代码+ChromeExtensionStage5: 向 background 请求标签页上下文；若没有这行代码，页面无法验证扩展是否能读取 tabs。
  chrome.runtime.sendMessage({ action: "tabs_context" }, (response) => {
    // 新增代码+ChromeExtensionStage5: 把响应格式化到页面；若没有这行代码，用户看不到调试输出。
    output.textContent = JSON.stringify(response, null, 2);
  });
});
