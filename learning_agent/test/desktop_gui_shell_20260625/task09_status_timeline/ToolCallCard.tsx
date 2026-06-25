type ToolCallCardProps = { // 新增代码+DesktopToolTimeline：定义工具卡片 props；如果没有这段，工具事件展示字段不清楚。
  eventType: string; // 新增代码+DesktopToolTimeline：保存事件类型；如果没有这行，用户不知道工具处于哪个阶段。
  toolName: string; // 新增代码+DesktopToolTimeline：保存工具名称；如果没有这行，卡片没有主标题。
  summary: string; // 新增代码+DesktopToolTimeline：保存工具摘要；如果没有这行，用户看不到工具在做什么。
}; // 新增代码+DesktopToolTimeline：props 类型结束；如果没有这行，TypeScript 类型语法不完整。

export function ToolCallCard({ eventType, toolName, summary }: ToolCallCardProps): JSX.Element { // 新增代码+DesktopToolTimeline：函数段开始，渲染工具事件卡片；如果没有这段，工具进度只能混在普通状态列表里。
  return ( // 新增代码+DesktopToolTimeline：返回卡片结构；如果没有这行，组件不会输出 UI。
    <article className="tool-card"> {/* 新增代码+DesktopToolTimeline：定义工具卡片容器；如果没有这行，工具事件没有独立视觉块。 */}
      <div className="tool-card-title">{toolName}</div> {/* 新增代码+DesktopToolTimeline：显示工具名称；如果没有这行，用户不知道哪个工具被调用。 */}
      <div className="tool-card-meta">{eventType}</div> {/* 新增代码+DesktopToolTimeline：显示事件类型；如果没有这行，用户不知道是 started、completed 还是 failed。 */}
      <p>{summary}</p> {/* 新增代码+DesktopToolTimeline：显示工具摘要；如果没有这行，卡片没有可读上下文。 */}
    </article> // 新增代码+DesktopToolTimeline：工具卡片容器结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+DesktopToolTimeline：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+DesktopToolTimeline：函数段结束，ToolCallCard 到此结束；如果没有这个边界，初学者不易看出卡片范围。
