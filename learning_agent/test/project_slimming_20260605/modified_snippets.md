# 项目瘦身修改学习备份

## 修改目标

本次修改 `.gitignore` 是为了防止真实终端验收截图、Windows Computer Use 证据、JSONL 事件流和学习备份图片继续进入仓库状态，避免项目再次从几十 MB 膨胀到接近 1 GB。

## 新增规则片段

```gitignore
# 新增代码+项目瘦身：忽略 Windows Computer Use 截图证据目录；如果没有这行，真实桌面截图和 BMP 证据会继续进入 Git 状态，让项目体积快速变大。
learning_agent/memory/computer_use/evidence/
# 新增代码+项目瘦身：忽略 harness 运行事件目录；如果没有这行，长期任务每次运行产生的 JSONL 事件会持续堆进项目，后续排查和提交都会变慢。
learning_agent/memory/harness/events/
# 新增代码+项目瘦身：忽略根目录 memory 的会话记录；如果没有这行，外层运行记录也会继续留下 transcript 和事件流，项目会再次膨胀。
memory/sessions/
# 新增代码+项目瘦身：忽略根目录 memory 的状态事件；如果没有这行，状态 JSONL 会随着每次运行增长，仓库会被运行历史拖大。
memory/status/
# 新增代码+项目瘦身：忽略学习备份中的验收截图目录；如果没有这行，learning_agent/test 里会继续复制可见终端截图，学习目录会越来越大。
learning_agent/test/**/acceptance_run/
# 新增代码+项目瘦身：忽略学习备份中的可见终端截图目录；如果没有这行，visible terminal 截图会被保存进学习目录，项目体积会反复膨胀。
learning_agent/test/**/visible_terminal_run/
# 新增代码+项目瘦身：忽略学习备份中的 PNG 图片；如果没有这行，截图类学习附件会进入 Git 状态，源码仓库会被图片文件拖大。
learning_agent/test/**/*.png
# 新增代码+项目瘦身：忽略学习备份中的 BMP 图片；如果没有这行，未压缩 BMP 截图可能单个就占数 MB，让 agent 项目显得异常臃肿。
learning_agent/test/**/*.bmp
# 新增代码+项目瘦身：忽略学习备份中的 JPG/JPEG 图片；如果没有这行，浏览器或桌面验收图片会继续污染学习备份目录。
learning_agent/test/**/*.jpg
# 新增代码+项目瘦身：忽略学习备份中的 JPEG 图片；如果没有这行，不同后缀的同类截图仍可能漏网进入仓库。
learning_agent/test/**/*.jpeg
# 新增代码+项目瘦身：忽略学习备份中的 WebP 图片；如果没有这行，浏览器产出的 WebP 证据也会继续增加项目体积。
learning_agent/test/**/*.webp
# 新增代码+项目瘦身：忽略学习备份中的 JSONL 事件流；如果没有这行，学习目录会复制大量逐行日志，后续阅读和提交都会变重。
learning_agent/test/**/*.jsonl
```
