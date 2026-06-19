import pytest  # 新增代码+LayerSkillLoaderTest：导入 pytest 验证拒绝路径；如果没有这行代码，异常门禁无法测试。

from learning_agent.computer_use_mcp_v2.windows_runtime.layer_skill_loader import DEFAULT_MAX_PROMPT_CHARS, load_layer_skill  # 新增代码+LayerSkillLoaderTest：导入内部 layer loader；如果没有这行代码，测试无法覆盖安全加载。


def test_loader_reads_only_internal_layer_skill_metadata() -> None:  # 新增代码+LayerSkillLoaderTest：函数段开始，验证 loader 返回稳定元数据；如果没有这段测试，prompt 版本证据可能缺失。
    prompt = load_layer_skill("intent_understanding")  # 新增代码+LayerSkillLoaderTest：加载意图理解层提示；如果没有这行代码，正向路径没有覆盖。
    assert prompt.layer_name == "intent_understanding"  # 新增代码+LayerSkillLoaderTest：确认层名正确；如果没有这行断言，loader 可能读错层。
    assert prompt.relative_path == "intent_understanding/SKILL.md"  # 新增代码+LayerSkillLoaderTest：确认路径是内部相对路径；如果没有这行断言，证据可能暴露绝对路径。
    assert len(prompt.content_sha256_16) == 16  # 新增代码+LayerSkillLoaderTest：确认短哈希存在；如果没有这行断言，版本不可追踪。
    assert "structured desktop intent" in prompt.content  # 新增代码+LayerSkillLoaderTest：确认内容来自意图层文件；如果没有这行断言，可能读到错误文件。
    assert "content" not in prompt.metadata()  # 新增代码+LayerSkillLoaderTest：确认公开 metadata 不含正文；如果没有这行断言，运行证据可能泄露提示词全文。
    # 新增代码+LayerSkillLoaderTest：函数段结束，test_loader_reads_only_internal_layer_skill_metadata 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_loader_rejects_path_traversal_and_unknown_layer() -> None:  # 新增代码+LayerSkillLoaderTest：函数段开始，验证路径穿越和未知层被拒绝；如果没有这段测试，loader 可能越界读文件。
    with pytest.raises(ValueError):  # 新增代码+LayerSkillLoaderTest：期待未知层抛错；如果没有这行代码，异常路径无法验证。
        load_layer_skill("../intent_understanding")  # 新增代码+LayerSkillLoaderTest：尝试通过层名穿越；如果没有这行代码，穿越门禁没有触发条件。
    with pytest.raises(ValueError):  # 新增代码+LayerSkillLoaderTest：期待非法文件名抛错；如果没有这行代码，文件白名单无法验证。
        load_layer_skill("intent_understanding", "../README.md")  # 新增代码+LayerSkillLoaderTest：尝试通过文件名穿越；如果没有这行代码，文件路径门禁没有触发条件。
    # 新增代码+LayerSkillLoaderTest：函数段结束，test_loader_rejects_path_traversal_and_unknown_layer 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_loader_rejects_oversized_prompt_budget() -> None:  # 新增代码+LayerSkillLoaderTest：函数段开始，验证 max_chars 生效；如果没有这段测试，超大 prompt 可能进入上下文。
    assert DEFAULT_MAX_PROMPT_CHARS > 100  # 新增代码+LayerSkillLoaderTest：确认默认预算不是无意义小值；如果没有这行断言，测试配置可能失真。
    with pytest.raises(ValueError):  # 新增代码+LayerSkillLoaderTest：期待小预算触发拒绝；如果没有这行代码，超限路径无法验证。
        load_layer_skill("intent_understanding", max_chars=8)  # 新增代码+LayerSkillLoaderTest：用极小预算加载文件；如果没有这行代码，超限门禁不会触发。
    # 新增代码+LayerSkillLoaderTest：函数段结束，test_loader_rejects_oversized_prompt_budget 到此结束；如果没有这个边界说明，用户不容易看出测试范围。


def test_loader_can_read_batch_execution_contract() -> None:  # 新增代码+LayerSkillLoaderTest：函数段开始，验证 batch_execution 读 CONTRACT；如果没有这段测试，确定性执行契约可能读错文件。
    prompt = load_layer_skill("batch_execution")  # 新增代码+LayerSkillLoaderTest：加载批执行契约；如果没有这行代码，batch_execution 特例未覆盖。
    assert prompt.relative_path == "batch_execution/CONTRACT.md"  # 新增代码+LayerSkillLoaderTest：确认默认文件是 CONTRACT；如果没有这行断言，executor 可能被误当成 prompt 层。
    assert "not a reasoning layer" in prompt.content  # 新增代码+LayerSkillLoaderTest：确认契约强调非推理层；如果没有这行断言，内容可能读错。
    # 新增代码+LayerSkillLoaderTest：函数段结束，test_loader_can_read_batch_execution_contract 到此结束；如果没有这个边界说明，用户不容易看出测试范围。
