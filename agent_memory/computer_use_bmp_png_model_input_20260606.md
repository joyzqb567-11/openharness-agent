# 2026-06-06 Computer Use BMP 截图转 PNG 输入模型

## 背景
- 真实可见终端 controller 场景已经能让 `/computer use --full` 进入真实 Paint 窗口观察。
- 失败点不是“没有截图”，而是 Windows observe 落盘截图为 BMP。
- OAuth/Responses API 报错：`image/bmp` 不是支持的输入图片格式。

## 根因
- `LearningAgent._computer_use_image_blocks_from_tool_output()` 之前直接读取 artifact 原始字节并按 `image/bmp` 生成 data URL。
- `CodexOAuthChatModel` 会把该 data URL 转成 Responses `input_image`。
- Responses API 支持 PNG/JPEG/GIF/WebP，不支持 BMP，所以真实终端任务在模型看到截图前就 HTTP 400。

## 修复
- 新增 `_computer_use_model_image_payload()` 统一生成“模型兼容图片字节 + MIME”。
- 新增 `_computer_use_png_payload_from_bmp_artifact()`，用 Pillow 把 BMP artifact 真实转码为 PNG。
- 保留空图、超大图、读取失败、转码失败的 observation 记录，避免静默失败。
- 新增 `test_agent_converts_bmp_computer_use_screenshot_to_png_model_image_block`，要求 data URL MIME 是 PNG，并且解码后字节拥有 PNG 文件头。

## 自动化验证
- 红灯：新增 BMP 测试在修复前失败，失败点为 data URL 不是 `data:image/png;base64,`。
- 绿灯：同一测试修复后通过。
- 回归：`python -m unittest learning_agent.tests.test_models_codex_oauth learning_agent.tests.test_windows_computer_use_image_results_phase41` 通过，54 tests OK。
- 编译：`python -m py_compile learning_agent\core\agent.py learning_agent\models\adapters.py learning_agent\tests\test_windows_computer_use_image_results_phase41.py learning_agent\tests\test_models_codex_oauth.py` 通过。

## 待验收
- 仍需用 controller 重新启动真实可见 `start_oauth_agent.bat`，输入 `/computer use --full` 和“请使用本地电脑的画图软件画一棵树。”。
- 只有真实终端场景通过后，才允许说本轮真实验收通过。
