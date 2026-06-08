// 新增代码+ChromeExtensionStage5: 预留页面桥文件用于未来 Stage 6 写动作隔离；若没有这行代码，manifest 目录缺少蓝图要求的 page_bridge.js。
window.__OPENHARNESS_READONLY_BRIDGE__ = {
  // 新增代码+ChromeExtensionStage5: 暴露只读模式标记；若没有这行代码，调试时无法确认当前桥没有写动作。
  mode: "read_only"
};
