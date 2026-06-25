type PermissionBannerProps = { // 新增代码+DesktopGUIPermissions：定义权限提示条 props；如果没有这段，调用方不知道要传标题和说明。
  title: string; // 新增代码+DesktopGUIPermissions：保存提示标题；如果没有这行，banner 无法快速说明当前需要用户处理。
  detail: string; // 新增代码+DesktopGUIPermissions：保存提示详情；如果没有这行，banner 只能显示空泛提醒。
}; // 新增代码+DesktopGUIPermissions：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function PermissionBanner({ title, detail }: PermissionBannerProps): JSX.Element { // 新增代码+DesktopGUIPermissions：函数段开始，渲染权限提示条；如果没有这段，用户可能错过正在等待的权限请求。
  return ( // 新增代码+DesktopGUIPermissions：返回权限提示条结构；如果没有这行，组件不会输出 UI。
    <section className="permission-banner" role="status"> {/* 新增代码+DesktopGUIPermissions：定义状态提示区域；如果没有这行，读屏器和用户都难以注意权限等待。 */}
      <strong>{title}</strong> {/* 新增代码+DesktopGUIPermissions：显示权限提示标题；如果没有这行，banner 不够醒目。 */}
      <span>{detail}</span> {/* 新增代码+DesktopGUIPermissions：显示权限提示详情；如果没有这行，用户不知道请求来自哪个工具或应用。 */}
    </section> // 新增代码+DesktopGUIPermissions：权限提示条区域结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIPermissions：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopGUIPermissions：函数段结束，PermissionBanner 到此结束；如果没有这个边界，初学者不易看出提示条范围。
