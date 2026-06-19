"""Safe loader for Computer Use internal layer skill prompts."""  # 新增代码+LayerSkillLoader：说明本文件只加载 Computer Use 内部层提示词；如果没有这行代码，读者可能误以为它会调用全局 skill_load。
from __future__ import annotations  # 新增代码+LayerSkillLoader：启用延迟类型解析；如果没有这行代码，类型注解在旧启动方式下更容易失败。

import hashlib  # 新增代码+LayerSkillLoader：导入哈希工具生成 prompt 版本摘要；如果没有这行代码，证据无法稳定说明加载了哪个版本。
from dataclasses import dataclass  # 新增代码+LayerSkillLoader：导入数据类减少 loader 返回对象样板；如果没有这行代码，返回结构会变成散乱 dict。
from pathlib import Path  # 新增代码+LayerSkillLoader：导入 Path 安全处理 Windows 路径；如果没有这行代码，路径拼接和父目录校验容易出错。
from typing import Any  # 新增代码+LayerSkillLoader：导入 Any 描述 JSON 元数据；如果没有这行代码，公开方法类型边界不清楚。


LAYER_SKILL_ROOT = Path(__file__).resolve().parents[1] / "layer_skills"  # 新增代码+LayerSkillLoader：固定内部 layer_skills 根目录；如果没有这行代码，loader 可能读到全局技能目录。
LAYER_SKILL_DEFAULT_FILES = {"intent_understanding": "SKILL.md", "stage_planning": "SKILL.md", "observation": "SKILL.md", "verification": "SKILL.md", "reflection_learning": "SKILL.md", "batch_execution": "CONTRACT.md"}  # 新增代码+LayerSkillLoader：定义允许层和默认文件；如果没有这行代码，未知层名可能被拿来路径穿越。
LAYER_SKILL_ALLOWED_FILES = frozenset({"SKILL.md", "OUTPUT_SCHEMA.md", "CONTRACT.md"})  # 新增代码+LayerSkillLoader：定义可读文件名白名单；如果没有这行代码，调用方可能读取目录内任意文件。
DEFAULT_MAX_PROMPT_CHARS = 12000  # 新增代码+LayerSkillLoader：限制单个 prompt 文件大小；如果没有这行代码，异常大文件会挤爆上下文。


@dataclass(frozen=True)  # 新增代码+LayerSkillLoader：声明加载结果不可变；如果没有这行代码，后续层可能意外修改 prompt 元数据。
class LayerSkillPrompt:  # 新增代码+LayerSkillLoader：类段开始，保存一次内部 layer prompt 加载结果；如果没有这个类，元数据和内容会散在多个返回字段里。
    layer_name: str  # 新增代码+LayerSkillLoader：保存层名；如果没有这行代码，调用方无法知道 prompt 属于哪个层。
    relative_path: str  # 新增代码+LayerSkillLoader：保存相对路径；如果没有这行代码，证据无法审计 prompt 来源。
    content_sha256_16: str  # 新增代码+LayerSkillLoader：保存内容短哈希；如果没有这行代码，版本变化难以追踪。
    content: str  # 新增代码+LayerSkillLoader：保存 prompt 内容；如果没有这行代码，调用方无法使用内部层提示。

    def metadata(self) -> dict[str, Any]:  # 新增代码+LayerSkillLoader：函数段开始，返回不含 prompt 正文的元数据；如果没有这段函数，公开 evidence 可能泄露提示词全文。
        return {"layer_name": self.layer_name, "relative_path": self.relative_path, "content_sha256_16": self.content_sha256_16}  # 新增代码+LayerSkillLoader：返回低敏元数据；如果没有这行代码，运行报告无法证明加载版本。
    # 新增代码+LayerSkillLoader：函数段结束，LayerSkillPrompt.metadata 到此结束；如果没有这个边界说明，用户不容易看出元数据范围。
# 新增代码+LayerSkillLoader：类段结束，LayerSkillPrompt 到此结束；如果没有这个边界说明，用户不容易看出加载结果类范围。


def _layer_skill_clean_name(value: str) -> str:  # 新增代码+LayerSkillLoader：函数段开始，清理层名或文件名；如果没有这段函数，空白和反斜杠可能影响白名单判断。
    return str(value or "").replace("\\", "/").strip()  # 新增代码+LayerSkillLoader：统一路径分隔符并去空白；如果没有这行代码，Windows 反斜杠穿越不易发现。
# 新增代码+LayerSkillLoader：函数段结束，_layer_skill_clean_name 到此结束；如果没有这个边界说明，用户不容易看出清理范围。


def _layer_skill_hash(content: str) -> str:  # 新增代码+LayerSkillLoader：函数段开始，计算内容短哈希；如果没有这段函数，多个调用点会重复写哈希逻辑。
    return hashlib.sha256(content.encode("utf-8", "replace")).hexdigest()[:16]  # 新增代码+LayerSkillLoader：返回 16 位 sha256 摘要；如果没有这行代码，prompt 元数据不稳定。
# 新增代码+LayerSkillLoader：函数段结束，_layer_skill_hash 到此结束；如果没有这个边界说明，用户不容易看出哈希范围。


def load_layer_skill(layer_name: str, relative_file: str | None = None, max_chars: int = DEFAULT_MAX_PROMPT_CHARS) -> LayerSkillPrompt:  # 新增代码+LayerSkillLoader：函数段开始，安全加载一个内部层提示词；如果没有这段函数，runtime 会手工读文件并可能越界。
    clean_layer = _layer_skill_clean_name(layer_name)  # 新增代码+LayerSkillLoader：清理层名；如果没有这行代码，空白或反斜杠会污染白名单。
    if clean_layer not in LAYER_SKILL_DEFAULT_FILES:  # 新增代码+LayerSkillLoader：拒绝未知层名；如果没有这行代码，调用方可能通过层名读取任意目录。
        raise ValueError(f"unknown Computer Use layer skill: {clean_layer}")  # 新增代码+LayerSkillLoader：抛出稳定错误；如果没有这行代码，未知层会变成难懂的 FileNotFoundError。
    clean_file = _layer_skill_clean_name(relative_file or LAYER_SKILL_DEFAULT_FILES[clean_layer])  # 新增代码+LayerSkillLoader：选择默认文件或调用方指定文件；如果没有这行代码，OUTPUT_SCHEMA 无法按需加载。
    if "/" in clean_file or ".." in clean_file or clean_file not in LAYER_SKILL_ALLOWED_FILES:  # 新增代码+LayerSkillLoader：拒绝路径穿越和非白名单文件；如果没有这行代码，loader 可能越过 layer_skills 根目录。
        raise ValueError("layer skill file must be a known file name inside the layer folder")  # 新增代码+LayerSkillLoader：返回明确错误；如果没有这行代码，穿越失败原因不清楚。
    prompt_path = (LAYER_SKILL_ROOT / clean_layer / clean_file).resolve()  # 新增代码+LayerSkillLoader：解析目标文件绝对路径；如果没有这行代码，后续无法确认文件还在根目录内。
    root_path = LAYER_SKILL_ROOT.resolve()  # 新增代码+LayerSkillLoader：解析根目录绝对路径；如果没有这行代码，父目录校验可能被相对路径绕过。
    if root_path not in prompt_path.parents:  # 新增代码+LayerSkillLoader：确认目标文件仍在内部根目录下；如果没有这行代码，符号链接或奇怪路径可能绕过。
        raise ValueError("layer skill path escaped internal root")  # 新增代码+LayerSkillLoader：发现越界时拒绝；如果没有这行代码，安全边界会失效。
    content = prompt_path.read_text(encoding="utf-8")  # 新增代码+LayerSkillLoader：读取 UTF-8 prompt 文件；如果没有这行代码，调用方拿不到提示内容。
    if len(content) > int(max_chars):  # 新增代码+LayerSkillLoader：检查文件长度；如果没有这行代码，过大 prompt 会撑爆模型上下文。
        raise ValueError("layer skill prompt is too large")  # 新增代码+LayerSkillLoader：拒绝超大文件；如果没有这行代码，loader 会悄悄截断造成行为漂移。
    relative_path = f"{clean_layer}/{clean_file}"  # 新增代码+LayerSkillLoader：构造稳定相对路径；如果没有这行代码，metadata 可能暴露本机绝对路径。
    return LayerSkillPrompt(layer_name=clean_layer, relative_path=relative_path, content_sha256_16=_layer_skill_hash(content), content=content)  # 新增代码+LayerSkillLoader：返回内容和低敏元数据；如果没有这行代码，调用方没有统一结果对象。
# 新增代码+LayerSkillLoader：函数段结束，load_layer_skill 到此结束；如果没有这个边界说明，用户不容易看出安全加载范围。


__all__ = ["DEFAULT_MAX_PROMPT_CHARS", "LAYER_SKILL_DEFAULT_FILES", "LayerSkillPrompt", "load_layer_skill"]  # 新增代码+LayerSkillLoader：声明公开接口；如果没有这行代码，通配导入会暴露内部 helper。
