type PermissionDialogProps = { // 新增代码+DesktopGUIPermissions：定义权限弹窗 props；如果没有这段，调用方不知道弹窗需要哪些字段。
  open: boolean; // 新增代码+DesktopGUIPermissions：控制弹窗是否打开；如果没有这行，权限弹窗会一直显示或无法显示。
  requestId: string; // 新增代码+DesktopGUIPermissions：保存后端权限 request_id；如果没有这行，用户无法看到正在回答哪个请求。
  appName: string; // 新增代码+DesktopGUIPermissions：保存应用或工具名；如果没有这行，用户不知道谁在请求权限。
  reason: string; // 新增代码+DesktopGUIPermissions：保存请求原因；如果没有这行，用户无法判断是否应该允许。
  riskSummary: string; // 新增代码+DesktopGUIPermissions：保存风险摘要；如果没有这行，安全上下文会缺失。
  onApprove: () => void; // 新增代码+DesktopGUIPermissions：保存允许回调；如果没有这行，允许按钮没有动作。
  onDeny: () => void; // 新增代码+DesktopGUIPermissions：保存拒绝回调；如果没有这行，拒绝按钮没有动作。
}; // 新增代码+DesktopGUIPermissions：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function PermissionDialog({ open, requestId, appName, reason, riskSummary, onApprove, onDeny }: PermissionDialogProps): JSX.Element | null { // 新增代码+DesktopGUIPermissions：函数段开始，渲染权限确认弹窗；如果没有这段，GUI 无法让用户明确允许或拒绝。
  if (!open) { // 新增代码+DesktopGUIPermissions：未打开时不渲染弹窗；如果没有这行，页面会一直被遮罩覆盖。
    return null; // 新增代码+DesktopGUIPermissions：关闭状态返回空；如果没有这行，React 会继续渲染弹窗结构。
  } // 新增代码+DesktopGUIPermissions：打开状态判断结束；如果没有这行，条件块语法不完整。
  return ( // 新增代码+DesktopGUIPermissions：返回弹窗结构；如果没有这行，组件不会输出 UI。
    <div className="permission-dialog-backdrop"> {/* 新增代码+DesktopGUIPermissions：定义弹窗遮罩；如果没有这行，权限请求会和主界面混在一起。 */}
      <section className="permission-dialog" role="dialog" aria-modal="true" aria-label="权限请求"> {/* 新增代码+DesktopGUIPermissions：定义可访问的权限对话框；如果没有这行，读屏器无法识别模态确认。 */}
        <h2>权限请求</h2> {/* 新增代码+DesktopGUIPermissions：显示弹窗标题；如果没有这行，用户不清楚当前是安全确认。 */}
        <dl className="permission-dialog-details"> {/* 新增代码+DesktopGUIPermissions：使用键值对展示请求详情；如果没有这行，request_id 和风险信息会缺少结构。 */}
          <dt>请求</dt> {/* 新增代码+DesktopGUIPermissions：标记 request id 字段名；如果没有这行，用户不知道下一行是什么。 */}
          <dd>{requestId}</dd> {/* 新增代码+DesktopGUIPermissions：显示后端 request_id；如果没有这行，用户无法把弹窗和审计事件对上。 */}
          <dt>应用/工具</dt> {/* 新增代码+DesktopGUIPermissions：标记应用工具字段名；如果没有这行，用户不知道权限来源。 */}
          <dd>{appName}</dd> {/* 新增代码+DesktopGUIPermissions：显示应用或工具名；如果没有这行，用户不知道谁要权限。 */}
          <dt>原因</dt> {/* 新增代码+DesktopGUIPermissions：标记原因字段名；如果没有这行，请求说明缺少语义。 */}
          <dd>{reason}</dd> {/* 新增代码+DesktopGUIPermissions：显示后端提供的脱敏原因；如果没有这行，用户无法判断是否允许。 */}
          <dt>风险</dt> {/* 新增代码+DesktopGUIPermissions：标记风险字段名；如果没有这行，风险摘要缺少语义。 */}
          <dd>{riskSummary}</dd> {/* 新增代码+DesktopGUIPermissions：显示风险摘要；如果没有这行，用户可能在无风险提示下点击允许。 */}
        </dl> {/* 新增代码+DesktopGUIPermissions：请求详情列表结束；如果没有这行，JSX 结构不完整。 */}
        <div className="permission-dialog-actions"> {/* 新增代码+DesktopGUIPermissions：定义按钮区域；如果没有这行，允许和拒绝按钮没有稳定布局。 */}
          <button className="permission-deny-button" type="button" onClick={onDeny}>拒绝</button> {/* 新增代码+DesktopGUIPermissions：渲染拒绝按钮；如果没有这行，用户无法明确阻止权限。 */}
          <button className="permission-approve-button" type="button" onClick={onApprove}>允许</button> {/* 新增代码+DesktopGUIPermissions：渲染允许按钮；如果没有这行，用户无法批准需要的操作。 */}
        </div> {/* 新增代码+DesktopGUIPermissions：按钮区域结束；如果没有这行，JSX 结构不完整。 */}
      </section> {/* 新增代码+DesktopGUIPermissions：权限对话框结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 新增代码+DesktopGUIPermissions：弹窗遮罩结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopGUIPermissions：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopGUIPermissions：函数段结束，PermissionDialog 到此结束；如果没有这个边界，初学者不易看出权限弹窗范围。
