type PermissionDialogProps = { // 修改代码+DesktopGUIPermissionsV2：定义权限弹窗 props；如果没有这段，调用方不知道弹窗需要哪些字段。
  open: boolean; // 修改代码+DesktopGUIPermissionsV2：控制弹窗是否打开；如果没有这行，权限弹窗会一直显示或无法显示。
  requestId: string; // 修改代码+DesktopGUIPermissionsV2：保存后端权限 request_id；如果没有这行，用户无法看到正在回答哪个请求。
  toolName: string; // 新增代码+DesktopGUIPermissionsV2：保存具体工具名；如果没有这行，用户只能看到应用名，无法判断是哪条工具轨道在请求。
  appName: string; // 修改代码+DesktopGUIPermissionsV2：保存应用名；如果没有这行，用户不知道谁在请求权限。
  actionSummary: string; // 新增代码+DesktopGUIPermissionsV2：保存动作摘要；如果没有这行，弹窗只能显示零散字段，用户理解成本更高。
  reason: string; // 修改代码+DesktopGUIPermissionsV2：保存请求原因；如果没有这行，用户无法判断是否应该允许。
  riskSummary: string; // 修改代码+DesktopGUIPermissionsV2：保存风险摘要；如果没有这行，安全上下文会缺失。
  decisionPending: boolean; // 新增代码+DesktopGUIPermissionsV2：保存决策是否正在提交；如果没有这行，用户双击按钮可能制造重复请求。
  onApprove: () => void; // 修改代码+DesktopGUIPermissionsV2：保存允许回调；如果没有这行，允许按钮没有动作。
  onDeny: () => void; // 修改代码+DesktopGUIPermissionsV2：保存拒绝回调；如果没有这行，拒绝按钮没有动作。
}; // 修改代码+DesktopGUIPermissionsV2：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function PermissionDialog({ open, requestId, toolName, appName, actionSummary, reason, riskSummary, decisionPending, onApprove, onDeny }: PermissionDialogProps): JSX.Element | null { // 修改代码+DesktopGUIPermissionsV2：函数段开始，渲染权限确认弹窗；如果没有这段，GUI 无法让用户明确允许或拒绝。
  if (!open) { // 修改代码+DesktopGUIPermissionsV2：未打开时不渲染弹窗；如果没有这行，页面会一直被遮罩覆盖。
    return null; // 修改代码+DesktopGUIPermissionsV2：关闭状态返回空；如果没有这行，React 会继续渲染弹窗结构。
  } // 修改代码+DesktopGUIPermissionsV2：打开状态判断结束；如果没有这行，条件块语法不完整。
  return ( // 修改代码+DesktopGUIPermissionsV2：返回弹窗结构；如果没有这行，组件不会输出 UI。
    <div className="permission-dialog-backdrop"> {/* 修改代码+DesktopGUIPermissionsV2：定义弹窗遮罩；如果没有这行，权限请求会和主界面混在一起。 */}
      <section className="permission-dialog" role="dialog" aria-modal="true" aria-label="权限请求"> {/* 修改代码+DesktopGUIPermissionsV2：定义可访问的权限对话框；如果没有这行，读屏器无法识别模态确认。 */}
        <h2>权限请求</h2> {/* 修改代码+DesktopGUIPermissionsV2：显示弹窗标题；如果没有这行，用户不清楚当前是安全确认。 */}
        <dl className="permission-dialog-details"> {/* 修改代码+DesktopGUIPermissionsV2：使用键值对展示请求详情；如果没有这行，request_id 和风险信息会缺少结构。 */}
          <dt>请求</dt> {/* 修改代码+DesktopGUIPermissionsV2：标记 request id 字段名；如果没有这行，用户不知道下一行是什么。 */}
          <dd>{requestId}</dd> {/* 修改代码+DesktopGUIPermissionsV2：显示后端 request_id；如果没有这行，用户无法把弹窗和审计事件对上。 */}
          <dt>应用</dt> {/* 修改代码+DesktopGUIPermissionsV2：标记应用字段名；如果没有这行，用户不知道权限来自哪个应用外壳。 */}
          <dd>{appName}</dd> {/* 修改代码+DesktopGUIPermissionsV2：显示应用名；如果没有这行，用户不知道哪个应用在请求权限。 */}
          <dt>工具</dt> {/* 新增代码+DesktopGUIPermissionsV2：标记具体工具字段名；如果没有这行，用户无法区分浏览器、终端或桌面自动化请求。 */}
          <dd>{toolName}</dd> {/* 新增代码+DesktopGUIPermissionsV2：显示具体工具名；如果没有这行，权限来源会过于模糊。 */}
          <dt>动作</dt> {/* 新增代码+DesktopGUIPermissionsV2：标记动作摘要字段名；如果没有这行，用户只能读长 reason 来理解请求。 */}
          <dd>{actionSummary}</dd> {/* 新增代码+DesktopGUIPermissionsV2：显示后端整理好的动作摘要；如果没有这行，弹窗缺少最短决策信息。 */}
          <dt>原因</dt> {/* 修改代码+DesktopGUIPermissionsV2：标记原因字段名；如果没有这行，请求说明缺少语义。 */}
          <dd>{reason}</dd> {/* 修改代码+DesktopGUIPermissionsV2：显示后端提供的脱敏原因；如果没有这行，用户无法判断是否允许。 */}
          <dt>风险</dt> {/* 修改代码+DesktopGUIPermissionsV2：标记风险字段名；如果没有这行，风险摘要缺少语义。 */}
          <dd>{riskSummary}</dd> {/* 修改代码+DesktopGUIPermissionsV2：显示风险摘要；如果没有这行，用户可能在无风险提示下点击允许。 */}
        </dl> {/* 修改代码+DesktopGUIPermissionsV2：请求详情列表结束；如果没有这行，JSX 结构不完整。 */}
        <div className="permission-dialog-actions"> {/* 修改代码+DesktopGUIPermissionsV2：定义按钮区域；如果没有这行，允许和拒绝按钮没有稳定布局。 */}
          <button className="permission-deny-button" type="button" disabled={decisionPending} aria-disabled={decisionPending} onClick={onDeny}>{decisionPending ? "提交中" : "拒绝"}</button> {/* 修改代码+DesktopGUIPermissionsV2：渲染带等待态的拒绝按钮；如果没有这行，用户可能重复拒绝同一权限。 */}
          <button className="permission-approve-button" type="button" disabled={decisionPending} aria-disabled={decisionPending} onClick={onApprove}>{decisionPending ? "提交中" : "允许"}</button> {/* 修改代码+DesktopGUIPermissionsV2：渲染带等待态的允许按钮；如果没有这行，用户可能重复允许同一权限。 */}
        </div> {/* 修改代码+DesktopGUIPermissionsV2：按钮区域结束；如果没有这行，JSX 结构不完整。 */}
      </section> {/* 修改代码+DesktopGUIPermissionsV2：权限对话框结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 修改代码+DesktopGUIPermissionsV2：弹窗遮罩结束；如果没有这行，JSX 结构不完整。
  ); // 修改代码+DesktopGUIPermissionsV2：返回语句结束；如果没有这行，函数没有返回边界。
} // 修改代码+DesktopGUIPermissionsV2：函数段结束，PermissionDialog 到此结束；如果没有这个边界，初学者不易看出权限弹窗范围。
