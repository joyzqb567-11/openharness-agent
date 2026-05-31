# Experience

## 2026-05-28 长回答验收断言经验

- 经验：真实终端验收不能只用 `answer_preview` 判断最终回答是否包含关键字段，因为长回答很容易在 500 字预览处截断。
- 建议：事件 payload 同时保留 `answer_preview` 和 `answer_text`；`answer_preview` 用于快速看摘要，`answer_text` 用于机器断言。
- 建议：controller 需要兼容旧事件，若没有 `answer_text` 再回退到 `answer_preview`，避免历史 run 证据无法读取。
- 建议：当工具日志和最终回答日志都显示成功，而 controller 只在 event answer check 失败时，优先排查事件预览截断或事件字段不足，不要先怀疑浏览器动作失败。

## 2026-05-28 真实浏览器自然查询识别经验

- 经验：公开查询任务不能只匹配“查询/搜索”这类动词，用户经常会说“某网站的视频、评论最多、有哪些、排行、介绍”等问句；这类表达也必须进入真实浏览器客户模式，否则会重新出现多次 `y/N`。
- 建议：修复此类问题时必须用用户截图里的原始短 prompt 做红灯测试，再跑真实可见终端验收并检查 `permission_sent_count=0`。
- 建议：已经启动的旧 `start_oauth_agent.bat` 进程不会热加载代码，权限体验类修复完成后要提醒用户重启终端再复测。
