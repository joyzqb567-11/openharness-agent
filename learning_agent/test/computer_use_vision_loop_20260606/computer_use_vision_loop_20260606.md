# Computer Use Vision Loop 2026-06-06

## 本轮治本结论

- 已把 Computer Use 工具结果中的截图 artifact 从“文本路径证据”升级为模型主循环可见的 `image_url` 图片消息。
- 已把 `CodexOAuthChatModel` 的 Responses 请求输入从纯文本 prompt 升级为“文本 prompt + 原生 `input_image` 图片块”。
- 文本 prompt 会保留工具 schema 和对话结构，但会把图片 data URL 替换为占位说明，避免 base64 重复进入文本上下文。
- 这一步对齐 ClaudeCode 的关键设计：模型下一轮能看到用户自然语言、工具 schema、工具结果，以及真实截图像素，再自行决定下一步工具调用。

## 已验证

- `python -m unittest learning_agent.tests.test_models_codex_oauth learning_agent.tests.test_windows_computer_use_image_results_phase41`
- `python -m py_compile learning_agent\core\agent.py learning_agent\models\adapters.py learning_agent\tests\test_windows_computer_use_image_results_phase41.py learning_agent\tests\test_models_codex_oauth.py`

## 尚未完成

- 真实可见终端交互验收还没有在本轮完成。
- 不能仅凭本轮自动化测试声明 `/computer use --full` 已成熟。
- 下一步应启动 `learning_agent\start_oauth_agent.bat` 的本地可见终端，让用户输入 `/computer use --full` 和真实自然语言任务，例如“请使用本地电脑的画图软件画一棵树。”，观察是否真的启动画图、截图回灌、模型规划、鼠标键盘动作、纠偏闭环。
