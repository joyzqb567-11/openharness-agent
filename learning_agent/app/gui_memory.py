"""Read-only memory, prompt, token, and notebook payloads for the Desktop GUI."""  # 新增代码+DesktopGUIMemoryPanel：说明本模块只负责右侧记忆面板的只读摘要；如果没有这行，维护者容易把它误当成可写记忆入口。

from __future__ import annotations  # 新增代码+DesktopGUIMemoryPanel：启用延迟类型解析；如果没有这行，较新的类型注解在部分入口里可能提前求值失败。

import os  # 新增代码+DesktopGUIMemoryPanel：扫描 notebook 文件时需要安全遍历目录；如果没有这行，notebook 状态只能靠硬编码假数据。
from datetime import UTC, datetime  # 新增代码+DesktopGUIMemoryPanel：生成 UTC 时间戳；如果没有这行，前端无法判断记忆状态是否新鲜。
from pathlib import Path  # 新增代码+DesktopGUIMemoryPanel：规范化 workspace 和 agent_memory 路径；如果没有这行，Windows 路径拼接容易出错。
from typing import Any  # 新增代码+DesktopGUIMemoryPanel：标注通用 JSON payload；如果没有这行，函数返回结构边界不清楚。

from learning_agent.app.gui_context import gui_context_limits_from_env  # 新增代码+DesktopGUIMemoryPanel：复用 GUI 上下文预算配置；如果没有这行，token 面板会和真实上下文构建阈值分裂。
from learning_agent.app.gui_diagnostics import redact_diagnostic_text  # 新增代码+DesktopGUIMemoryPanel：复用诊断脱敏逻辑；如果没有这行，记忆预览可能泄露 token 或本机路径。
from learning_agent.app.gui_protocol import GUI_V2_SCHEMA_VERSION  # 新增代码+DesktopGUIMemoryPanel：复用 V2 schema 版本；如果没有这行，memory endpoint 会和其它 GUI payload 漂移。
from learning_agent.runtime.status_snapshot import build_status_snapshot  # 新增代码+DesktopGUIMemoryPanel：读取统一状态快照摘要；如果没有这行，prompt/token 状态无法反映真实 compact/resume 线索。
from learning_agent.tools.catalog import build_builtin_tool_catalog  # 新增代码+DesktopGUIMemoryPanel：复用真实工具目录；如果没有这行，prompt/notebook 工具可用性会变成前端猜测。


MEMORY_FILE_MAX_BYTES = 128_000  # 新增代码+DesktopGUIMemoryPanel：限制单个记忆文件读取字节；如果没有这行，大型 progress 文件可能拖慢 GUI。
MEMORY_PREVIEW_LINE_LIMIT = 6  # 新增代码+DesktopGUIMemoryPanel：限制 GUI 预览行数；如果没有这行，长期进度会把右侧面板撑爆。
MEMORY_HEADING_LIMIT = 6  # 新增代码+DesktopGUIMemoryPanel：限制最近标题数量；如果没有这行，长文档标题列表会淹没核心状态。
MEMORY_NOTEBOOK_LIMIT = 12  # 新增代码+DesktopGUIMemoryPanel：限制返回 notebook 示例数量；如果没有这行，大量 notebook 会让 payload 过大。
MEMORY_NOTEBOOK_SCAN_LIMIT = 300  # 新增代码+DesktopGUIMemoryPanel：限制 notebook 扫描计数上限；如果没有这行，大仓库首次打开可能卡住。
MEMORY_NOTEBOOK_SKIP_DIRS = {".git", ".codegraph", ".pytest_cache", ".ruff_cache", ".venv", "venv", "node_modules", ".worktrees", "__pycache__", "learning_agent/test"}  # 新增代码+DesktopGUIMemoryPanel：声明扫描时跳过的重目录；如果没有这行，GUI 会浪费时间扫依赖和历史副本。
MEMORY_FILES = (("context", "Context", Path("agent_memory/context.md")), ("progress", "Progress", Path("agent_memory/progress.md")), ("bugs", "Bugs", Path("agent_memory/bugs.md")), ("experience", "Experience", Path("agent_memory/experience.md")))  # 新增代码+DesktopGUIMemoryPanel：声明长期记忆固定文件；如果没有这行，面板不知道应该显示哪些不跑偏文档。
PROMPT_TOOL_NAMES = ("prompt_surface_report", "token_budget_report")  # 新增代码+DesktopGUIMemoryPanel：声明 prompt/token 状态关注的工具名；如果没有这行，面板无法校验真实报告工具是否注册。
NOTEBOOK_TOOL_NAMES = ("notebook_read", "notebook_edit")  # 新增代码+DesktopGUIMemoryPanel：声明 notebook 状态关注的工具名；如果没有这行，面板无法校验 notebook 工具链是否接入。


def _workspace_path(workspace: str | Path) -> Path:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，统一规范化 workspace；如果没有这段，多处路径处理会重复且容易不一致。
    return Path(workspace).expanduser().resolve()  # 新增代码+DesktopGUIMemoryPanel：返回解析后的绝对工作区路径；如果没有这行，相对路径会导致读取错误目录。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_workspace_path 到此结束；如果没有这个边界，用户不容易看出路径规范化范围。


def _generated_at() -> str:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，生成统一时间戳；如果没有这段，三个 endpoint 的时间格式可能不一致。
    return datetime.now(UTC).isoformat()  # 新增代码+DesktopGUIMemoryPanel：返回 UTC ISO 字符串；如果没有这行，前端无法展示稳定刷新时间。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_generated_at 到此结束；如果没有这个边界，用户不容易看出时间生成范围。


def _safe_text(value: Any, fallback: str = "", limit: int = 220) -> str:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，把未知字段变成脱敏短文本；如果没有这段，None、token 或长路径可能污染 GUI。
    if value is None:  # 新增代码+DesktopGUIMemoryPanel：先处理空值；如果没有这行，Python None 会显示成难懂的 "None"。
        return fallback  # 新增代码+DesktopGUIMemoryPanel：空值使用人话兜底；如果没有这行，空字段会让前端再写兜底逻辑。
    text = redact_diagnostic_text(value).replace("\r", " ").strip()  # 新增代码+DesktopGUIMemoryPanel：复用脱敏并去掉无意义空白；如果没有这行，敏感文本或多余换行可能进入摘要。
    if not text:  # 新增代码+DesktopGUIMemoryPanel：识别清理后的空文本；如果没有这行，空字符串会继续往下走。
        return fallback  # 新增代码+DesktopGUIMemoryPanel：空文本返回兜底；如果没有这行，界面会出现空白状态。
    return text[:limit] + ("..." if len(text) > limit else "")  # 新增代码+DesktopGUIMemoryPanel：限制文本长度并提示截断；如果没有这行，长记忆行可能撑破右侧栏。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_safe_text 到此结束；如果没有这个边界，用户不容易看出文本安全范围。


def _relative_path(workspace_path: Path, path: Path) -> str:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，把路径压成 workspace 相对路径；如果没有这段，payload 可能泄露本机绝对路径。
    try:  # 新增代码+DesktopGUIMemoryPanel：保护 relative_to 计算；如果没有这行，异常路径会导致 endpoint 失败。
        return path.resolve().relative_to(workspace_path).as_posix()  # 新增代码+DesktopGUIMemoryPanel：返回正斜杠相对路径；如果没有这行，前端会看到平台相关路径。
    except ValueError:  # 新增代码+DesktopGUIMemoryPanel：处理路径不在 workspace 内的情况；如果没有这行，越界路径会抛异常。
        return "[outside-workspace]"  # 新增代码+DesktopGUIMemoryPanel：越界时返回安全占位；如果没有这行，本机绝对路径可能进入 GUI。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_relative_path 到此结束；如果没有这个边界，用户不容易看出路径脱敏范围。


def _count_lines(path: Path) -> int:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，统计记忆文件行数；如果没有这段，GUI 无法判断文档规模。
    try:  # 新增代码+DesktopGUIMemoryPanel：保护文件读取；如果没有这行，锁文件或编码问题会让整个面板失败。
        with path.open("r", encoding="utf-8", errors="replace") as handle:  # 新增代码+DesktopGUIMemoryPanel：以 UTF-8 容错读取文本；如果没有这行，中文记忆文件可能在异常字节处失败。
            return sum(1 for _line in handle)  # 新增代码+DesktopGUIMemoryPanel：按行累计数量；如果没有这行，line_count 没有事实来源。
    except OSError:  # 新增代码+DesktopGUIMemoryPanel：处理文件暂时不可读；如果没有这行，权限或锁错误会冒泡到 HTTP。
        return 0  # 新增代码+DesktopGUIMemoryPanel：不可读时返回 0；如果没有这行，降级 payload 无法继续生成。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_count_lines 到此结束；如果没有这个边界，用户不容易看出行数读取范围。


def _read_file_tail(path: Path, size_bytes: int) -> tuple[str, bool]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，读取文件尾部用于展示最近进度；如果没有这段，大文件只能全量读或只能看开头。
    if size_bytes > MEMORY_FILE_MAX_BYTES:  # 新增代码+DesktopGUIMemoryPanel：判断文件是否过大；如果没有这行，大型进度文件会被整份读入。
        with path.open("rb") as handle:  # 新增代码+DesktopGUIMemoryPanel：用二进制读取尾部；如果没有这行，无法精确控制读取字节数。
            handle.seek(max(0, size_bytes - MEMORY_FILE_MAX_BYTES))  # 新增代码+DesktopGUIMemoryPanel：移动到安全尾部窗口；如果没有这行，大文件仍会从头读取。
            return handle.read(MEMORY_FILE_MAX_BYTES).decode("utf-8", errors="replace"), True  # 新增代码+DesktopGUIMemoryPanel：返回尾部文本并标记截断；如果没有这行，前端不知道预览不是全文。
    return path.read_text(encoding="utf-8", errors="replace"), False  # 新增代码+DesktopGUIMemoryPanel：小文件直接读取全文；如果没有这行，普通记忆文件无法预览。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_read_file_tail 到此结束；如果没有这个边界，用户不容易看出大文件保护范围。


def _preview_lines(text: str) -> list[str]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，生成最近非空行预览；如果没有这段，GUI 要展示原始全文或空白。
    lines = [_safe_text(line, "", 220) for line in text.splitlines() if _safe_text(line, "", 220)]  # 新增代码+DesktopGUIMemoryPanel：清洗并过滤空行；如果没有这行，预览会混入空白或敏感文本。
    return lines[-MEMORY_PREVIEW_LINE_LIMIT:]  # 新增代码+DesktopGUIMemoryPanel：只返回最后几行；如果没有这行，右侧面板会显示过多历史。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_preview_lines 到此结束；如果没有这个边界，用户不容易看出预览生成范围。


def _heading_lines(text: str) -> list[str]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，提取最近 Markdown 标题；如果没有这段，用户很难扫视长期文档结构。
    headings = [_safe_text(line.lstrip("#").strip(), "", 180) for line in text.splitlines() if line.lstrip().startswith("#")]  # 新增代码+DesktopGUIMemoryPanel：收集标题文本并脱敏；如果没有这行，标题区没有事实来源。
    return [heading for heading in headings if heading][-MEMORY_HEADING_LIMIT:]  # 新增代码+DesktopGUIMemoryPanel：过滤空标题并限制数量；如果没有这行，标题列表可能过长。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_heading_lines 到此结束；如果没有这个边界，用户不容易看出标题提取范围。


def _memory_file_summary(workspace_path: Path, file_id: str, label: str, relative_path: Path) -> dict[str, Any]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，生成单个 agent_memory 文件摘要；如果没有这段，面板无法稳定展示 context/progress/bugs。
    path = workspace_path / relative_path  # 新增代码+DesktopGUIMemoryPanel：拼出真实文件路径；如果没有这行，无法检查文件是否存在。
    base_payload: dict[str, Any] = {"id": file_id, "label": label, "relative_path": relative_path.as_posix(), "exists": False, "status": "missing", "size_bytes": 0, "line_count": 0, "truncated": False, "preview_lines": [], "headings": [], "safe_error": ""}  # 新增代码+DesktopGUIMemoryPanel：准备稳定空态；如果没有这行，缺文件时前端字段会缺失。
    if not path.exists():  # 新增代码+DesktopGUIMemoryPanel：处理首次运行缺少记忆文件；如果没有这行，stat/read 会抛 FileNotFoundError。
        return base_payload  # 新增代码+DesktopGUIMemoryPanel：缺文件返回安全空态；如果没有这行，正常空项目会被误报成失败。
    if not path.is_file():  # 新增代码+DesktopGUIMemoryPanel：防止同名目录被当成 Markdown 读取；如果没有这行，目录会触发底层读取错误。
        return {**base_payload, "exists": True, "status": "not_file", "safe_error": "记忆路径存在但不是文件。"}  # 新增代码+DesktopGUIMemoryPanel：返回目录异常摘要；如果没有这行，用户不知道为什么不可读。
    try:  # 新增代码+DesktopGUIMemoryPanel：保护 stat 和读取过程；如果没有这行，临时权限错误会拖垮全部 memory endpoint。
        size_bytes = path.stat().st_size  # 新增代码+DesktopGUIMemoryPanel：读取文件大小；如果没有这行，面板无法判断记忆规模。
        text, truncated = _read_file_tail(path, size_bytes)  # 新增代码+DesktopGUIMemoryPanel：读取安全文本窗口；如果没有这行，预览没有输入。
        return {**base_payload, "exists": True, "status": "ready", "size_bytes": size_bytes, "line_count": _count_lines(path), "truncated": truncated, "preview_lines": _preview_lines(text), "headings": _heading_lines(text)}  # 新增代码+DesktopGUIMemoryPanel：返回完整白名单摘要；如果没有这行，前端拿不到记忆文件事实。
    except OSError as error:  # 新增代码+DesktopGUIMemoryPanel：捕获读取失败；如果没有这行，锁文件或权限问题会变成 HTTP 500。
        return {**base_payload, "exists": True, "status": "unreadable", "safe_error": _safe_text(error, "记忆文件暂时不可读。", 180)}  # 新增代码+DesktopGUIMemoryPanel：返回脱敏失败原因；如果没有这行，原始异常可能泄露本机路径。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_memory_file_summary 到此结束；如果没有这个边界，用户不容易看出文件白名单范围。


def _tool_map() -> dict[str, Any]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，按名称索引真实工具目录；如果没有这段，多个 endpoint 会重复遍历 catalog。
    return {tool.name: tool for tool in build_builtin_tool_catalog()}  # 新增代码+DesktopGUIMemoryPanel：构建 name 到 AgentTool 的映射；如果没有这行，工具可用性无法快速判断。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_tool_map 到此结束；如果没有这个边界，用户不容易看出工具索引范围。


def _tool_status(name: str, tools: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，生成单个工具状态；如果没有这段，prompt/notebook 状态会直接暴露内部对象。
    tool = tools.get(name)  # 新增代码+DesktopGUIMemoryPanel：从真实 catalog 查找工具；如果没有这行，状态无法对应实际注册表。
    if tool is None:  # 新增代码+DesktopGUIMemoryPanel：处理工具未注册；如果没有这行，后续属性读取会报错。
        return {"name": name, "available": False, "status": "unavailable", "read_only": False, "destructive": False, "source": "", "safe_unavailable_reason": "当前工具目录没有注册该工具。"}  # 新增代码+DesktopGUIMemoryPanel：返回稳定不可用状态；如果没有这行，前端无法解释缺失工具。
    return {"name": name, "available": True, "status": "ready" if getattr(tool, "always_load", False) else "deferred", "read_only": bool(getattr(tool, "is_read_only", False)), "destructive": bool(getattr(tool, "is_destructive", False)), "source": _safe_text(getattr(tool, "source", ""), "builtin", 120), "safe_unavailable_reason": ""}  # 新增代码+DesktopGUIMemoryPanel：返回白名单工具元数据；如果没有这行，UI 无法展示真实工具注册状态。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_tool_status 到此结束；如果没有这个边界，用户不容易看出工具状态范围。


def _safe_snapshot_summary(workspace_path: Path) -> dict[str, Any]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，读取 compact/resume 相关快照摘要；如果没有这段，token 状态缺少真实运行线索。
    try:  # 新增代码+DesktopGUIMemoryPanel：保护状态快照读取；如果没有这行，状态锁或坏 JSON 会让 prompt endpoint 失败。
        snapshot = build_status_snapshot(workspace_path)  # 新增代码+DesktopGUIMemoryPanel：复用统一状态快照；如果没有这行，GUI 会和 CLI 状态事实源分裂。
    except Exception as error:  # 新增代码+DesktopGUIMemoryPanel：捕获快照失败；如果没有这行，错误会冒泡到 HTTP。
        return {"status": "degraded", "safe_error": _safe_text(error, "状态快照暂时不可读。", 180), "compact": {}, "resume": {}, "counts": {}}  # 新增代码+DesktopGUIMemoryPanel：返回脱敏降级摘要；如果没有这行，前端无法显示安全失败状态。
    compact = snapshot.get("compact", {}) if isinstance(snapshot, dict) else {}  # 新增代码+DesktopGUIMemoryPanel：读取 compact 区块；如果没有这行，压缩状态没有输入。
    resume = snapshot.get("resume", {}) if isinstance(snapshot, dict) else {}  # 新增代码+DesktopGUIMemoryPanel：读取 resume 区块；如果没有这行，恢复状态没有输入。
    counts = snapshot.get("counts", {}) if isinstance(snapshot, dict) else {}  # 新增代码+DesktopGUIMemoryPanel：读取计数字段；如果没有这行，事件/任务规模不可见。
    return {"status": "ready", "safe_error": "", "compact": compact if isinstance(compact, dict) else {}, "resume": resume if isinstance(resume, dict) else {}, "counts": counts if isinstance(counts, dict) else {}}  # 新增代码+DesktopGUIMemoryPanel：返回白名单父级摘要；如果没有这行，调用方要重复类型收敛。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_safe_snapshot_summary 到此结束；如果没有这个边界，用户不容易看出快照摘要范围。


def _skip_notebook_dir(directory_path: Path) -> bool:  # 修改代码+DesktopGUIMemoryPanel：函数段开始，用完整目录路径判断 notebook 扫描是否跳过；如果没有这段，扫描会进入依赖、worktree 和学习归档副本。
    normalized_parts = directory_path.as_posix().split("/")  # 修改代码+DesktopGUIMemoryPanel：把目录拆成统一斜杠片段；如果没有这行，Windows 反斜杠会让 learning_agent/test 过滤失效。
    directory_name = directory_path.name  # 修改代码+DesktopGUIMemoryPanel：保留最后一段目录名用于兼容原有排除列表；如果没有这行，node_modules 等普通目录名无法快速过滤。
    return directory_name in MEMORY_NOTEBOOK_SKIP_DIRS or directory_name.startswith(".") or ("learning_agent" in normalized_parts and "test" in normalized_parts)  # 修改代码+DesktopGUIMemoryPanel：同时跳过重目录、隐藏目录和学习归档；如果没有这行，真实 GUI 刷新可能被大量副本拖慢。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_skip_notebook_dir 到此结束；如果没有这个边界，用户不容易看出扫描排除规则。


def _scan_notebooks(workspace_path: Path) -> dict[str, Any]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，扫描工作区 notebook 摘要；如果没有这段，Notebook 面板无法显示真实文件可见性。
    notebooks: list[str] = []  # 新增代码+DesktopGUIMemoryPanel：准备保存少量示例路径；如果没有这行，扫描结果没有容器。
    seen_count = 0  # 新增代码+DesktopGUIMemoryPanel：记录已发现 notebook 数量；如果没有这行，摘要栏无法显示规模。
    limited = False  # 新增代码+DesktopGUIMemoryPanel：记录扫描是否触顶；如果没有这行，用户无法知道数量是否被截断。
    try:  # 新增代码+DesktopGUIMemoryPanel：保护 os.walk；如果没有这行，权限错误会拖垮 endpoint。
        for root, dirs, files in os.walk(workspace_path):  # 新增代码+DesktopGUIMemoryPanel：逐层遍历工作区；如果没有这行，无法发现 notebook 文件。
            dirs[:] = [directory for directory in dirs if not _skip_notebook_dir(Path(root) / directory)]  # 修改代码+DesktopGUIMemoryPanel：原地按完整路径过滤子目录；如果没有这行，learning_agent/test 这种嵌套目录仍会被扫描。
            for filename in files:  # 新增代码+DesktopGUIMemoryPanel：遍历当前目录文件；如果没有这行，扫描不会处理任何文件。
                if not filename.lower().endswith(".ipynb"):  # 新增代码+DesktopGUIMemoryPanel：只关注 notebook 文件；如果没有这行，普通文件会污染 notebook 状态。
                    continue  # 新增代码+DesktopGUIMemoryPanel：非 notebook 跳过；如果没有这行，后续会错误计数。
                seen_count += 1  # 新增代码+DesktopGUIMemoryPanel：记录发现数量；如果没有这行，notebook_count 永远为 0。
                if len(notebooks) < MEMORY_NOTEBOOK_LIMIT:  # 新增代码+DesktopGUIMemoryPanel：限制返回示例数量；如果没有这行，payload 可能过大。
                    notebooks.append(_relative_path(workspace_path, Path(root) / filename))  # 新增代码+DesktopGUIMemoryPanel：保存相对路径示例；如果没有这行，用户看不到 notebook 位于哪里。
                if seen_count >= MEMORY_NOTEBOOK_SCAN_LIMIT:  # 新增代码+DesktopGUIMemoryPanel：扫描数量达到上限；如果没有这行，极端仓库可能扫描太久。
                    limited = True  # 新增代码+DesktopGUIMemoryPanel：标记扫描受限；如果没有这行，前端会误以为 count 是精确总数。
                    return {"notebook_count": seen_count, "notebooks": notebooks, "scan_limited": limited, "safe_error": ""}  # 新增代码+DesktopGUIMemoryPanel：提前返回安全结果；如果没有这行，上限保护不会生效。
    except OSError as error:  # 新增代码+DesktopGUIMemoryPanel：捕获目录读取失败；如果没有这行，权限问题会变成 HTTP 500。
        return {"notebook_count": seen_count, "notebooks": notebooks, "scan_limited": limited, "safe_error": _safe_text(error, "Notebook 扫描暂时不可读。", 180)}  # 新增代码+DesktopGUIMemoryPanel：返回脱敏扫描错误；如果没有这行，原始路径可能泄露。
    return {"notebook_count": seen_count, "notebooks": notebooks, "scan_limited": limited, "safe_error": ""}  # 新增代码+DesktopGUIMemoryPanel：返回扫描完成摘要；如果没有这行，函数没有稳定输出。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，_scan_notebooks 到此结束；如果没有这个边界，用户不容易看出 notebook 扫描范围。


def build_gui_memory_summary_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，构建 agent_memory 只读摘要；如果没有这段，GUI 无法看到长期上下文、进度和风险。
    workspace_path = _workspace_path(workspace)  # 新增代码+DesktopGUIMemoryPanel：规范化 workspace；如果没有这行，记忆文件定位不稳定。
    files = [_memory_file_summary(workspace_path, file_id, label, relative_path) for file_id, label, relative_path in MEMORY_FILES]  # 新增代码+DesktopGUIMemoryPanel：生成四个记忆文件摘要；如果没有这行，面板没有 context/progress/bugs 数据。
    file_map = {item["id"]: item for item in files}  # 新增代码+DesktopGUIMemoryPanel：按 id 建立索引；如果没有这行，顶层快捷字段会重复查找。
    status_degraded = any(item.get("status") in {"unreadable", "not_file"} for item in files)  # 新增代码+DesktopGUIMemoryPanel：判断是否有文件读取降级；如果没有这行，用户会误以为所有记忆可信。
    safe_errors = [str(item.get("safe_error", "")) for item in files if item.get("safe_error")]  # 新增代码+DesktopGUIMemoryPanel：收集安全错误；如果没有这行，降级原因无法汇总。
    return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "generated_at": _generated_at(), "workspace_name": workspace_path.name or "OpenHarness", "reuse_module": "agent_memory", "memory_root": "agent_memory", "files": files, "context_summary": file_map.get("context", {}), "progress_summary": file_map.get("progress", {}), "bugs_summary": file_map.get("bugs", {}), "experience_summary": file_map.get("experience", {}), "status_degraded": status_degraded, "safe_error": "；".join(safe_errors)}  # 新增代码+DesktopGUIMemoryPanel：返回稳定 memory payload；如果没有这行，HTTP route 没有响应体。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，build_gui_memory_summary_payload 到此结束；如果没有这个边界，用户不容易看出 memory endpoint 范围。


def build_gui_prompt_status_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，构建 prompt 和 token 状态；如果没有这段，GUI 无法看到上下文预算和报告工具是否可用。
    workspace_path = _workspace_path(workspace)  # 新增代码+DesktopGUIMemoryPanel：规范化 workspace；如果没有这行，状态快照读取位置不稳定。
    tools = _tool_map()  # 新增代码+DesktopGUIMemoryPanel：读取真实工具目录；如果没有这行，报告工具状态无法确认。
    limits = gui_context_limits_from_env()  # 新增代码+DesktopGUIMemoryPanel：读取 GUI 上下文预算；如果没有这行，token 面板无法显示真实阈值。
    snapshot_summary = _safe_snapshot_summary(workspace_path)  # 新增代码+DesktopGUIMemoryPanel：读取 compact/resume 摘要；如果没有这行，预算状态缺少运行事实。
    prompt_tools = [_tool_status(name, tools) for name in PROMPT_TOOL_NAMES]  # 新增代码+DesktopGUIMemoryPanel：生成 prompt/token 工具状态；如果没有这行，面板不知道报告工具是否注册。
    available_tool_count = sum(1 for item in prompt_tools if item.get("available") is True)  # 新增代码+DesktopGUIMemoryPanel：统计可用报告工具；如果没有这行，摘要栏无法显示覆盖度。
    return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "generated_at": _generated_at(), "workspace_name": workspace_path.name or "OpenHarness", "reuse_module": "learning_agent.prompts.report_tools;learning_agent.app.gui_context", "tools": prompt_tools, "tool_count": len(prompt_tools), "available_tool_count": available_tool_count, "context_budget": {"max_messages": limits.max_messages, "max_chars": limits.max_chars, "source": "OPENHARNESS_GUI_CONTEXT_MAX_MESSAGES/OPENHARNESS_GUI_CONTEXT_MAX_CHARS"}, "prompt_surface": {"tool": "prompt_surface_report", "available": bool(tools.get("prompt_surface_report")), "include_block_text_default": False, "source": "learning_agent.prompts.report_tools.prompt_surface_report"}, "token_budget": {"tool": "token_budget_report", "available": bool(tools.get("token_budget_report")), "include_tools_default": True, "source": "learning_agent.prompts.report_tools.token_budget_report"}, "snapshot_summary": snapshot_summary, "status_degraded": snapshot_summary.get("status") == "degraded", "safe_error": str(snapshot_summary.get("safe_error", ""))}  # 新增代码+DesktopGUIMemoryPanel：返回稳定 prompt/token payload；如果没有这行，HTTP route 没有响应体。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，build_gui_prompt_status_payload 到此结束；如果没有这个边界，用户不容易看出 prompt 状态范围。


def build_gui_notebook_status_payload(workspace: str | Path) -> dict[str, Any]:  # 新增代码+DesktopGUIMemoryPanel：函数段开始，构建 notebook 只读状态；如果没有这段，GUI 无法知道 notebook_read/edit 是否接入。
    workspace_path = _workspace_path(workspace)  # 新增代码+DesktopGUIMemoryPanel：规范化 workspace；如果没有这行，扫描目录不稳定。
    tools = _tool_map()  # 新增代码+DesktopGUIMemoryPanel：读取真实工具目录；如果没有这行，notebook 工具状态会是硬编码。
    notebook_tools = [_tool_status(name, tools) for name in NOTEBOOK_TOOL_NAMES]  # 新增代码+DesktopGUIMemoryPanel：生成 notebook 工具摘要；如果没有这行，面板无法显示 read/edit 是否注册。
    scan = _scan_notebooks(workspace_path)  # 新增代码+DesktopGUIMemoryPanel：扫描 workspace 中的 notebook 示例；如果没有这行，notebook_count 没有事实来源。
    status_degraded = bool(scan.get("safe_error"))  # 新增代码+DesktopGUIMemoryPanel：把扫描错误变成降级状态；如果没有这行，用户会误信扫描完整。
    return {"ok": True, "schema_version": GUI_V2_SCHEMA_VERSION, "generated_at": _generated_at(), "workspace_name": workspace_path.name or "OpenHarness", "reuse_module": "learning_agent.tools.notebook_tools", "tools": notebook_tools, "tool_count": len(notebook_tools), "available_tool_count": sum(1 for item in notebook_tools if item.get("available") is True), "read_only_first_pass": True, "edit_exposed_in_gui": False, "notebook_count": scan["notebook_count"], "notebooks": scan["notebooks"], "scan_limited": scan["scan_limited"], "status_degraded": status_degraded, "safe_error": str(scan.get("safe_error", ""))}  # 新增代码+DesktopGUIMemoryPanel：返回稳定 notebook payload；如果没有这行，HTTP route 没有响应体。
# 新增代码+DesktopGUIMemoryPanel：函数段结束，build_gui_notebook_status_payload 到此结束；如果没有这个边界，用户不容易看出 notebook 状态范围。
