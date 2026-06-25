type PermissionBannerProps = { // 修改代码+DesktopGUIPermissionsV2：定义权限提示条 props；如果没有这段，调用方不知道要传哪些权限摘要。
  title: string; // 修改代码+DesktopGUIPermissionsV2：保存提示标题；如果没有这行，banner 无法快速说明当前需要用户处理。
  toolName: string; // 新增代码+DesktopGUIPermissionsV2：保存工具名；如果没有这行，banner 无法提示权限来自哪条工具轨道。
  actionSummary: string; // 新增代码+DesktopGUIPermissionsV2：保存动作摘要；如果没有这行，用户只能打开弹窗才知道请求内容。
  riskSummary: string; // 新增代码+DesktopGUIPermissionsV2：保存风险摘要；如果没有这行，banner 缺少安全判断依据。
  decisionPending: boolean; // 新增代码+DesktopGUIPermissionsV2：保存决策提交状态；如果没有这行，banner 无法提示按钮正在等待后端确认。
}; // 修改代码+DesktopGUIPermissionsV2：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function PermissionBanner({ title, toolName, actionSummary, riskSummary, decisionPending }: PermissionBannerProps): JSX.Element { // 修改代码+DesktopGUIPermissionsV2：函数段开始，渲染权限提示条；如果没有这段，用户可能错过正在等待的权限请求。
  return ( // 修改代码+DesktopGUIPermissionsV2：返回权限提示条结构；如果没有这行，组件不会输出 UI。
    <section className="permission-banner" role="status"> {/* 修改代码+DesktopGUIPermissionsV2：定义状态提示区域；如果没有这行，读屏器和用户都难以注意权限等待。 */}
      <strong>{title}</strong> {/* 修改代码+DesktopGUIPermissionsV2：显示权限提示标题；如果没有这行，banner 不够醒目。 */}
      <span>{actionSummary}</span> {/* 新增代码+DesktopGUIPermissionsV2：显示动作摘要；如果没有这行，主界面看不出为什么卡住。 */}
      <span>{toolName} · {riskSummary}</span> {/* 新增代码+DesktopGUIPermissionsV2：显示工具名和风险摘要；如果没有这行，用户缺少快速安全判断。 */}
      {decisionPending ? <em>正在提交决策</em> : null} {/* 新增代码+DesktopGUIPermissionsV2：提交中显示等待提示；如果没有这行，用户不知道按钮禁用是因为正在等后端。 */}
    </section> // 修改代码+DesktopGUIPermissionsV2：权限提示条区域结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopGUIPermissionsV2：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopGUIPermissionsV2：函数段结束，PermissionBanner 到此结束；如果没有这个边界，初学者不易看出提示条范围。
