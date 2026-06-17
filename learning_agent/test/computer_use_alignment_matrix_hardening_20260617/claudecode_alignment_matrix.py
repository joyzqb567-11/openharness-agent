"""Computer Use ClaudeCode 对齐验收矩阵。"""  # 新增代码+ClaudeCodeAlignmentMatrix：说明本文件负责单独判定 OpenHarness Computer Use 是否对齐 ClaudeCode；如果没有这一行，用户打开文件时不容易知道模块用途。
from __future__ import annotations  # 新增代码+ClaudeCodeAlignmentMatrix：启用稳定的延迟类型注解；如果没有这一行，部分类型标注在旧解释器中可能提前求值出错。
import argparse  # 新增代码+ClaudeCodeAlignmentMatrix：导入命令行参数解析工具；如果没有这一行，真实终端场景无法传入 repo-root 和 ClaudeCode 根目录。
import json  # 新增代码+ClaudeCodeAlignmentMatrix：导入 JSON 工具用于读写 manifest 和 scenario；如果没有这一行，矩阵证据无法结构化落盘。
from pathlib import Path  # 新增代码+ClaudeCodeAlignmentMatrix：导入路径对象用于跨目录定位证据；如果没有这一行，路径拼接会变成脆弱字符串操作。
from typing import Any  # 新增代码+ClaudeCodeAlignmentMatrix：导入动态字典类型；如果没有这一行，公开 API 的输入输出含义不够清楚。

COMPUTER_USE_CLAUDECODE_ALIGNMENT_MARKER = "COMPUTER_USE_CLAUDECODE_ALIGNMENT_READY"  # 新增代码+ClaudeCodeAlignmentMatrix：定义真实终端可匹配的稳定 marker；如果没有这一行，acceptance controller 无法可靠识别矩阵结论。
CLAUDECODE_ALIGNMENT_MISSING = "CLAUDECODE_ALIGNMENT_MISSING"  # 新增代码+ClaudeCodeAlignmentMatrix：定义严重缺口等级；如果没有这一行，源文件或能力缺失时没有明确低等级。
CLAUDECODE_ALIGNMENT_PARTIAL = "CLAUDECODE_ALIGNMENT_PARTIAL"  # 新增代码+ClaudeCodeAlignmentMatrix：定义部分对齐等级；如果没有这一行，缺最终可见终端 gate 时容易误报 parity。
CLAUDECODE_PARITY = "CLAUDECODE_PARITY"  # 新增代码+ClaudeCodeAlignmentMatrix：定义 ClaudeCode 对齐等级；如果没有这一行，14 项全部对齐后没有独立结论名。
CLAUDECODE_PARITY_OR_BETTER = "CLAUDECODE_PARITY_OR_BETTER"  # 新增代码+ClaudeCodeAlignmentMatrix：定义对齐或超过等级；如果没有这一行，未来出现超越证据时没有稳定等级名。
ALIGNMENT_MANIFEST = Path("learning_agent/memory/computer_use/claudecode_alignment/claudecode_alignment_evidence_20260613.json")  # 新增代码+ClaudeCodeAlignmentMatrix：固定机器可读 manifest 路径；如果没有这一行，后续成熟度判定器找不到矩阵证据。
ALIGNMENT_REPORT = Path("agent_memory/computer_use_claudecode_alignment_report_20260613.md")  # 新增代码+ClaudeCodeAlignmentMatrix：固定人类可读报告路径；如果没有这一行，用户后续无法直接查看对齐矩阵。
ALIGNMENT_SCENARIO = Path("learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_claudecode_alignment_matrix_visible_terminal.json")  # 新增代码+ClaudeCodeAlignmentMatrix：固定真实可见终端 scenario 路径；如果没有这一行，规则十七验收没有专门入口。
EXCLUDED_PLATFORM_DIFFERENCES = {  # 新增代码+AlignmentMatrixHardening：声明只作为说明的系统差异排除项；如果没有这段常量，macOS 专属能力可能被误算成 Windows 缺口。
    "macos_tcc": "ClaudeCode macOS TCC 权限不适用于 Windows。",  # 新增代码+AlignmentMatrixHardening：说明 TCC 是 macOS 专属权限模型；如果没有这一行，用户可能误以为 OpenHarness 缺 TCC。
    "swift_helper": "ClaudeCode Swift helper 是 macOS 原生实现，Windows 使用 Win32/UIA/SendInput 等等价能力。",  # 新增代码+AlignmentMatrixHardening：说明 Swift helper 不属于 Windows 对齐目标；如果没有这一行，矩阵边界会不清楚。
    "external_mcp_package_internals": "外部 MCP 包内部代码不属于 OpenHarness 仓库可控范围。",  # 新增代码+AlignmentMatrixHardening：说明外部包内部实现不计入本仓库缺失；如果没有这一行，隐藏依赖会被当成可修复源码缺口。
}  # 新增代码+AlignmentMatrixHardening：系统差异排除项字典结束；如果没有这行代码，Python 字典语法不完整。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，_alignment_bool_token 统一布尔输出；如果没有这段函数，终端摘要里的 True/False 大小写会不稳定。
def _alignment_bool_token(value: Any) -> str:  # 新增代码+ClaudeCodeAlignmentMatrix：声明布尔 token helper；如果没有这一行，多个函数要重复处理布尔格式。
    return "true" if bool(value) else "false"  # 新增代码+ClaudeCodeAlignmentMatrix：返回小写 true/false；如果没有这一行，scenario 文本匹配可能因为大小写失败。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，_alignment_bool_token 到此结束；如果没有这个边界说明，初学者不容易看出格式化范围。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，_alignment_resolve 把相对路径固定到根目录；如果没有这段函数，命令从不同 cwd 运行时会读错文件。
def _alignment_resolve(root: str | Path, relative_path: str | Path) -> Path:  # 新增代码+ClaudeCodeAlignmentMatrix：声明路径解析函数；如果没有这一行，调用方要重复写 Path 拼接逻辑。
    candidate = Path(relative_path)  # 新增代码+ClaudeCodeAlignmentMatrix：把输入路径规范成 Path；如果没有这一行，字符串路径无法统一判断绝对/相对。
    return candidate if candidate.is_absolute() else Path(root) / candidate  # 新增代码+ClaudeCodeAlignmentMatrix：绝对路径原样返回，相对路径挂到根目录；如果没有这一行，ClaudeCode 根目录和 OpenHarness 根目录会混用。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，_alignment_resolve 到此结束；如果没有这个边界说明，用户不容易看出路径策略。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，_alignment_read_text 安全读取源码证据；如果没有这段函数，某个文件缺失会让整个矩阵崩溃。
def _alignment_read_text(root: str | Path, relative_path: str | Path) -> str:  # 新增代码+ClaudeCodeAlignmentMatrix：声明源码读取 helper；如果没有这一行，矩阵不能复用统一读取逻辑。
    source_path = _alignment_resolve(root, relative_path)  # 新增代码+ClaudeCodeAlignmentMatrix：先得到实际文件路径；如果没有这一行，后续无法打开正确文件。
    try:  # 新增代码+ClaudeCodeAlignmentMatrix：进入受保护读取区；如果没有这一行，缺文件或权限问题会直接中断矩阵。
        return source_path.read_text(encoding="utf-8", errors="replace")  # 新增代码+ClaudeCodeAlignmentMatrix：用 UTF-8 读取并容忍坏字符；如果没有这一行，少量编码异常会误伤整份报告。
    except OSError:  # 新增代码+ClaudeCodeAlignmentMatrix：捕获不可读文件；如果没有这一行，缺一份证据就不会生成可读失败项。
        return ""  # 新增代码+ClaudeCodeAlignmentMatrix：读取失败返回空文本；如果没有这一行，对应维度无法自然降级为 missing。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，_alignment_read_text 到此结束；如果没有这个边界说明，用户不容易看出错误处理范围。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，_alignment_files_contain_all 检查多文件 token；如果没有这段函数，每个维度会重复写文本拼接和 all 判断。
def _alignment_files_contain_all(root: str | Path, files: list[str], tokens: list[str]) -> bool:  # 新增代码+ClaudeCodeAlignmentMatrix：声明多文件 token 检查函数；如果没有这一行，矩阵没有统一源码证据规则。
    combined_text = "\n".join(_alignment_read_text(root, file_name) for file_name in files)  # 新增代码+ClaudeCodeAlignmentMatrix：把相关文件拼成一个证据文本；如果没有这一行，跨文件组合能力会被误判为缺失。
    return all(token in combined_text for token in tokens)  # 新增代码+ClaudeCodeAlignmentMatrix：要求所有 token 都存在才算具备能力；如果没有这一行，一个孤立词可能误报整个维度通过。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，_alignment_files_contain_all 到此结束；如果没有这个边界说明，用户不容易看出 token 检查范围。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，_alignment_load_json_file 读取已有验收证据；如果没有这段函数，CA13 等真实 evidence 只能靠字符串猜测。
def _alignment_load_json_file(root: str | Path, relative_path: str | Path) -> dict[str, Any]:  # 新增代码+ClaudeCodeAlignmentMatrix：声明 JSON 读取 helper；如果没有这一行，manifest 加载没有统一错误结构。
    payload_path = _alignment_resolve(root, relative_path)  # 新增代码+ClaudeCodeAlignmentMatrix：定位 JSON 文件；如果没有这一行，后续读取路径可能相对错位。
    if not payload_path.exists():  # 新增代码+ClaudeCodeAlignmentMatrix：先确认文件存在；如果没有这一行，缺失证据会变成底层异常。
        return {"load_ok": False, "load_error": f"missing:{payload_path}"}  # 新增代码+ClaudeCodeAlignmentMatrix：返回缺文件错误；如果没有这一行，报告无法说明缺哪份证据。
    try:  # 新增代码+ClaudeCodeAlignmentMatrix：保护 JSON 解析；如果没有这一行，坏 JSON 会让矩阵无法输出其它维度。
        payload = json.loads(payload_path.read_text(encoding="utf-8-sig"))  # 新增代码+ClaudeCodeAlignmentMatrix：兼容 UTF-8 BOM 读取 JSON；如果没有这一行，历史工具写出的 BOM 文件可能解析失败。
    except json.JSONDecodeError as error:  # 新增代码+ClaudeCodeAlignmentMatrix：捕获 JSON 格式错误；如果没有这一行，用户看不到证据损坏原因。
        return {"load_ok": False, "load_error": f"invalid_json:{error}"}  # 新增代码+ClaudeCodeAlignmentMatrix：返回格式错误说明；如果没有这一行，坏 manifest 会表现成不透明崩溃。
    if not isinstance(payload, dict):  # 新增代码+ClaudeCodeAlignmentMatrix：要求顶层必须是对象；如果没有这一行，列表或字符串会污染后续 .get 读取。
        return {"load_ok": False, "load_error": f"not_object:{payload_path}"}  # 新增代码+ClaudeCodeAlignmentMatrix：返回类型错误；如果没有这一行，异常结构不容易审计。
    payload["load_ok"] = True  # 新增代码+ClaudeCodeAlignmentMatrix：标记读取成功；如果没有这一行，调用方无法区分 false 字段和未加载状态。
    return payload  # 新增代码+ClaudeCodeAlignmentMatrix：返回证据对象；如果没有这一行，调用方拿不到 JSON 内容。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，_alignment_load_json_file 到此结束；如果没有这个边界说明，用户不容易看出证据读取边界。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，get_claudecode_alignment_dimensions 返回固定 14 项矩阵；如果没有这段函数，后续测试和报告没有统一维度清单。
def get_claudecode_alignment_dimensions() -> list[dict[str, Any]]:  # 新增代码+ClaudeCodeAlignmentMatrix：声明维度清单公开 API；如果没有这一行，其它模块无法复用对齐定义。
    return [  # 新增代码+ClaudeCodeAlignmentMatrix：开始返回维度列表；如果没有这一行，矩阵没有可迭代对象。
        {"id": "CA01", "name": "MCP request_access tool surface", "claudecode_files": ["utils/computerUse/setup.ts"], "claudecode_tokens": ["setupComputerUseMCP", "allowedTools", "mcp__computer-use__"], "openharness_evidence": ["learning_agent/tools/schemas.py", "learning_agent/computer_use_mcp_v2/windows_runtime/request_access_tool.py", "learning_agent/computer_use_mcp_v2/windows_runtime/top_level_governance_matrix.py"], "openharness_tokens": ["mcp__computer-use__request_access", "request_access", "mcp_request_access_tool_surface_gate"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA01 覆盖 MCP 授权工具面；如果没有这一项，模型是否先申请授权无法单独验收。
        {"id": "CA02", "name": "request_access session grants", "claudecode_files": ["utils/computerUse/wrapper.tsx"], "claudecode_tokens": ["getAllowedApps", "getGrantFlags", "runPermissionDialog"], "openharness_evidence": ["learning_agent/computer_use_mcp_v2/windows_runtime/session_context.py", "learning_agent/computer_use_mcp_v2/windows_runtime/persistent_grants.py", "learning_agent/computer_use_mcp_v2/windows_runtime/top_level_governance_matrix.py"], "openharness_tokens": ["allowed_apps", "grant_flags", "grant_scope_matches_target", "deny_action_without_request_access", "grant_expired", "grant_revoked"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA02 覆盖授权生命周期；如果没有这一项，工具面可能有但动作不受授权约束。
        {"id": "CA03", "name": "installed app inventory hardening", "claudecode_files": ["utils/computerUse/appNames.ts", "utils/computerUse/mcpServer.ts"], "claudecode_tokens": ["filterAppsForDescription", "APP_NAME_ALLOWED", "APP_NAME_MAX_COUNT", "tryGetInstalledAppNames"], "openharness_evidence": ["learning_agent/computer_use_mcp_v2/windows_runtime/windows_app_inventory.py", "learning_agent/computer_use_mcp_v2/windows_runtime/top_level_governance_matrix.py"], "openharness_tokens": ["sanitize_inventory_display_name", "APP_INVENTORY_HIGH_RISK_TOKENS", "APP_INVENTORY_BLOCKED_EXACT_NAMES", "installed_app_inventory_hardening_gate"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA03 覆盖应用清单过滤；如果没有这一项，高风险系统工具可能混进普通候选。
        {"id": "CA04", "name": "native permission diagnostics", "claudecode_files": ["utils/computerUse/hostAdapter.ts", "utils/computerUse/executor.ts"], "claudecode_tokens": ["ensureOsPermissions", "TCC"], "openharness_evidence": ["learning_agent/computer_use_mcp_v2/windows_runtime/native_permission_diagnostics.py", "learning_agent/computer_use_mcp_v2/windows_runtime/production_live_control.py", "learning_agent/computer_use_mcp_v2/windows_runtime/top_level_governance_matrix.py"], "openharness_tokens": ["ensureOsPermissions", "native_permission", "native_permission_diagnostics_gate"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA04 覆盖平台权限诊断；如果没有这一项，截图或输入权限缺失会被包装层掩盖。
        {"id": "CA05", "name": "display and coordinate state", "claudecode_files": ["utils/computerUse/wrapper.tsx", "utils/computerUse/executor.ts"], "claudecode_tokens": ["getSelectedDisplayId", "displayPinnedByModel", "getLastScreenshotDims", "getDisplaySize"], "openharness_evidence": ["learning_agent/computer_use_mcp_v2/windows_runtime/session_context.py", "learning_agent/computer_use_mcp_v2/windows_runtime/display_coordinate_session.py", "learning_agent/computer_use_mcp_v2/windows_runtime/top_level_governance_matrix.py"], "openharness_tokens": ["selected_display", "display_pinned", "last_screenshot_dims", "display_pin_coordinate_gate"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA05 覆盖显示器和坐标钉住；如果没有这一项，多屏场景容易点错位置。
        {"id": "CA06", "name": "model visible screenshots", "claudecode_files": ["utils/computerUse/wrapper.tsx"], "claudecode_tokens": ["type: 'image'", "base64", "media_type"], "openharness_evidence": ["learning_agent/computer_use_mcp_v2/windows_runtime/image_messages.py", "learning_agent/core/message_builders.py", "learning_agent/computer_use_mcp_v2/windows_runtime/top_level_governance_matrix.py"], "openharness_tokens": ["build_computer_use_image_blocks_from_tool_output", "image_url", "model_visible_screenshot_gate"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA06 覆盖模型可见截图块；如果没有这一项，agent 只能假装看见屏幕。
        {"id": "CA07", "name": "real desktop input dispatch", "claudecode_files": ["utils/computerUse/executor.ts"], "claudecode_tokens": ["click", "scroll", "drag", "type"], "openharness_evidence": ["learning_agent/computer_use_mcp_v2/windows_runtime/real_sendinput_guard.py", "learning_agent/computer_use_mcp_v2/windows_runtime/sendinput_executor.py", "learning_agent/memory/computer_use/post_parity/phase148c_fresh_benchmark_evidence_20260613.json"], "openharness_tokens": ["SendInput", "physical_dispatch", "real_sendinput"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA07 覆盖真实输入执行；如果没有这一项，recording sender 可能冒充真实桌面动作。
        {"id": "CA08", "name": "target identity and drift guard", "claudecode_files": ["utils/computerUse/executor.ts"], "claudecode_tokens": ["getFrontmostApp", "appUnderPoint"], "openharness_evidence": ["learning_agent/computer_use_mcp_v2/windows_runtime/target_identity.py", "learning_agent/computer_use_mcp_v2/windows_runtime/universal_target_session.py", "learning_agent/computer_use_mcp_v2/windows_runtime/closed_loop_executor.py"], "openharness_tokens": ["target_identity", "target_drift", "target_drift_blocks_action"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA08 覆盖目标身份和漂移阻断；如果没有这一项，窗口切换后可能误点用户窗口。
        {"id": "CA09", "name": "computer use lock and stale recovery", "claudecode_files": ["utils/computerUse/computerUseLock.ts", "utils/computerUse/wrapper.tsx"], "claudecode_tokens": ["checkComputerUseLock", "tryAcquireComputerUseLock", "releaseComputerUseLock", "stale"], "openharness_evidence": ["learning_agent/computer_use_mcp_v2/windows_runtime/lock.py", "learning_agent/computer_use_mcp_v2/windows_runtime/abort_streaming_hooks.py", "learning_agent/computer_use_mcp_v2/windows_runtime/top_level_governance_matrix.py"], "openharness_tokens": ["recover_stale_lock", "lock_released_after_recovery", "stale_lock_recovery_gate"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA09 覆盖互斥锁和陈旧锁恢复；如果没有这一项，崩溃后可能永久卡住 Computer Use。
        {"id": "CA10", "name": "global abort hotkey", "claudecode_files": ["utils/computerUse/escHotkey.ts", "utils/computerUse/wrapper.tsx"], "claudecode_tokens": ["registerEscHotkey", "unregisterEscHotkey"], "openharness_evidence": ["learning_agent/computer_use_mcp_v2/windows_runtime/global_escape_abort.py", "learning_agent/computer_use_mcp_v2/windows_runtime/abort_streaming_hooks.py", "learning_agent/computer_use_mcp_v2/windows_runtime/top_level_governance_matrix.py"], "openharness_tokens": ["GlobalEscapeAbortController", "registerEscHotkey", "global_escape_abort_gate"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA10 覆盖全局急停；如果没有这一项，长动作过程中用户无法快速止损。
        {"id": "CA11", "name": "turn cleanup and unhide", "claudecode_files": ["utils/computerUse/cleanup.ts"], "claudecode_tokens": ["cleanupComputerUseAfterTurn", "unregisterEscHotkey", "releaseComputerUseLock"], "openharness_evidence": ["learning_agent/computer_use_mcp_v2/windows_runtime/turn_cleanup.py", "learning_agent/computer_use_mcp_v2/windows_runtime/session_context.py", "learning_agent/computer_use_mcp_v2/windows_runtime/top_level_governance_matrix.py"], "openharness_tokens": ["cleanup_completed", "host_hide_cleanup_gate", "hidden_windows"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA11 覆盖回合结束清理；如果没有这一项，隐藏窗口、热键或锁可能跨回合残留。
        {"id": "CA12", "name": "tool rendering and status", "claudecode_files": ["utils/computerUse/toolRendering.tsx"], "claudecode_tokens": ["getComputerUseMCPRenderingOverrides", "Computer Use[", "RESULT_SUMMARY"], "openharness_evidence": ["learning_agent/app/computer_status_renderer.py", "learning_agent/computer_use_mcp_v2/windows_runtime/top_level_governance_matrix.py"], "openharness_tokens": ["Computer Use Tool Rendering", "allowed_apps", "screenshot", "tool_rendering_status_gate"]},  # 新增代码+ClaudeCodeAlignmentMatrix：CA12 覆盖工具状态渲染；如果没有这一项，用户看不清 agent 正在做什么和被授权什么。
        {"id": "CA13", "name": "7 of 7 real GUI benchmark support", "claudecode_files": ["utils/computerUse/executor.ts", "utils/computerUse/mcpServer.ts"], "claudecode_tokens": ["screenshot", "click", "request_access"], "openharness_evidence": ["learning_agent/memory/computer_use/post_parity/final_maturity_evidence_manifest_20260613.json", "learning_agent/memory/computer_use/post_parity/phase148c_fresh_benchmark_evidence_20260613.json"], "openharness_tokens": [], "special_gate": "phase148c_7_of_7"},  # 新增代码+ClaudeCodeAlignmentMatrix：CA13 覆盖 7/7 真实 GUI 基准；如果没有这一项，源码对齐不能说明真实场景覆盖度。
        {"id": "CA14", "name": "final visible terminal proof", "claudecode_files": ["utils/computerUse/setup.ts", "utils/computerUse/wrapper.tsx"], "claudecode_tokens": ["mcp__computer-use__", "runPermissionDialog"], "openharness_evidence": ["learning_agent/acceptance_controller/runs"], "openharness_tokens": [], "special_gate": "visible_terminal_gate"},  # 新增代码+ClaudeCodeAlignmentMatrix：CA14 覆盖最终真实可见终端验收；如果没有这一项，静态矩阵会绕过规则十七。
    ]  # 新增代码+ClaudeCodeAlignmentMatrix：结束维度列表；如果没有这一行，Python 列表语法不完整。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，get_claudecode_alignment_dimensions 到此结束；如果没有这个边界说明，用户不容易看出 14 项定义范围。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，_alignment_phase148c_gate 判断 7/7 真实 GUI 证据；如果没有这段函数，CA13 无法从真实 evidence 得到结论。
def _alignment_phase148c_gate(repo_root: str | Path) -> tuple[bool, dict[str, Any]]:  # 新增代码+ClaudeCodeAlignmentMatrix：声明 Phase148C gate helper；如果没有这一行，评估函数会混入太多特殊逻辑。
    manifest = _alignment_load_json_file(repo_root, "learning_agent/memory/computer_use/post_parity/final_maturity_evidence_manifest_20260613.json")  # 新增代码+ClaudeCodeAlignmentMatrix：读取最终成熟度 manifest；如果没有这一行，CA13 不知道最新 7/7 汇总。
    score = manifest.get("score", {}) if isinstance(manifest.get("score"), dict) else {}  # 新增代码+ClaudeCodeAlignmentMatrix：安全取出 score；如果没有这一行，坏 manifest 会导致 .get 异常。
    fresh_count = int(score.get("phase148c_fresh_real_gui_count", 0) or 0)  # 新增代码+ClaudeCodeAlignmentMatrix：读取真实 GUI 覆盖数量；如果没有这一行，7/7 无法计算。
    required_count = int(score.get("phase148c_required_count", 7) or 7)  # 新增代码+ClaudeCodeAlignmentMatrix：读取要求数量；如果没有这一行，未来扩展基准数量时矩阵会写死。
    failures_fixed = bool(score.get("phase148d_failures_fixed"))  # 新增代码+ClaudeCodeAlignmentMatrix：确认已知失败是否归零；如果没有这一行，带已知 bug 的 7/7 可能被误判对齐。
    gate_passed = bool(manifest.get("load_ok") and fresh_count >= required_count and required_count >= 7 and failures_fixed)  # 新增代码+ClaudeCodeAlignmentMatrix：汇总 CA13 是否通过；如果没有这一行，CA13 没有单一判断结果。
    return gate_passed, {"manifest_loaded": bool(manifest.get("load_ok")), "fresh_count": fresh_count, "required_count": required_count, "failures_fixed": failures_fixed}  # 新增代码+ClaudeCodeAlignmentMatrix：返回通过状态和细节；如果没有这一行，报告无法解释 CA13 结果。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，_alignment_phase148c_gate 到此结束；如果没有这个边界说明，用户不容易看出真实 GUI 基准规则。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，_alignment_visible_terminal_gate 判断最终可见终端证据；如果没有这段函数，CA14 无法防止静态证据误升 parity。
def _alignment_visible_terminal_gate(repo_root: str | Path, visible_terminal_gate: bool, final_visible_run_dir: str) -> tuple[str, dict[str, Any]]:  # 新增代码+ClaudeCodeAlignmentMatrix：声明可见终端 gate helper；如果没有这一行，评估函数要手动处理最终门禁。
    run_dir_text = str(final_visible_run_dir or "").strip()  # 新增代码+ClaudeCodeAlignmentMatrix：规范化 run 目录字符串；如果没有这一行，空白参数可能被当成有效路径。
    run_dir = _alignment_resolve(repo_root, run_dir_text) if run_dir_text else Path("")  # 新增代码+ClaudeCodeAlignmentMatrix：把相对 run 目录转成绝对候选；如果没有这一行，历史证据路径可能找错。
    run_exists = bool(run_dir_text and run_dir.exists() and run_dir.is_dir())  # 新增代码+ClaudeCodeAlignmentMatrix：确认 run 目录真实存在；如果没有这一行，随便传字符串也会被当成验收证据。
    aligned = bool(visible_terminal_gate and run_exists)  # 新增代码+ClaudeCodeAlignmentMatrix：只有显式 gate 和真实 run 目录同时满足才 aligned；如果没有这一行，CLI 自检会误升 parity。
    status = "aligned" if aligned else "partial"  # 新增代码+ClaudeCodeAlignmentMatrix：没有最终 gate 时降为 partial 而非 missing；如果没有这一行，开发中矩阵会把唯一待验收项误报成结构缺失。
    return status, {"visible_terminal_gate": bool(visible_terminal_gate), "final_visible_run_dir": run_dir_text, "final_visible_run_dir_exists": run_exists}  # 新增代码+ClaudeCodeAlignmentMatrix：返回状态和证据细节；如果没有这一行，报告无法追踪 CA14 边界。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，_alignment_visible_terminal_gate 到此结束；如果没有这个边界说明，用户不容易看出最终 gate 规则。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，_alignment_dimension_status 评估单个维度；如果没有这段函数，主评估函数会重复且难以审计。
def _alignment_dimension_status(dimension: dict[str, Any], repo_root: str | Path, claudecode_root: str | Path, visible_terminal_gate: bool, final_visible_run_dir: str) -> dict[str, Any]:  # 新增代码+ClaudeCodeAlignmentMatrix：声明单维度评估入口；如果没有这一行，矩阵不能逐项输出原因。
    special_gate = str(dimension.get("special_gate", ""))  # 新增代码+ClaudeCodeAlignmentMatrix：读取可选特殊 gate；如果没有这一行，CA13/CA14 无法走证据文件逻辑。
    claudecode_files = [str(item) for item in dimension.get("claudecode_files", [])]  # 新增代码+ClaudeCodeAlignmentMatrix：清洗 ClaudeCode 文件清单；如果没有这一行，坏维度结构会污染读取。
    claudecode_tokens = [str(item) for item in dimension.get("claudecode_tokens", [])]  # 新增代码+ClaudeCodeAlignmentMatrix：清洗 ClaudeCode token 清单；如果没有这一行，token 检查可能收到非字符串。
    openharness_files = [str(item) for item in dimension.get("openharness_evidence", []) if str(item) != "learning_agent/acceptance_controller/runs"]  # 新增代码+ClaudeCodeAlignmentMatrix：清洗 OpenHarness 文件证据并跳过目录证据；如果没有这一行，目录会被当文件读取。
    openharness_tokens = [str(item) for item in dimension.get("openharness_tokens", [])]  # 新增代码+ClaudeCodeAlignmentMatrix：清洗 OpenHarness token 清单；如果没有这一行，源码检查可能被坏值干扰。
    claudecode_ok = _alignment_files_contain_all(claudecode_root, claudecode_files, claudecode_tokens)  # 新增代码+ClaudeCodeAlignmentMatrix：检查 ClaudeCode 参考源码是否存在对应能力；如果没有这一行，对齐矩阵没有参照基准。
    openharness_ok = _alignment_files_contain_all(repo_root, openharness_files, openharness_tokens) if openharness_tokens else True  # 新增代码+ClaudeCodeAlignmentMatrix：检查 OpenHarness 侧普通源码 token；如果没有这一行，静态能力无法被核验。
    special_details: dict[str, Any] = {}  # 新增代码+ClaudeCodeAlignmentMatrix：准备保存特殊 gate 细节；如果没有这一行，CA13/CA14 的原因无法进入报告。
    if special_gate == "phase148c_7_of_7":  # 新增代码+ClaudeCodeAlignmentMatrix：处理 7/7 真实 GUI 特殊维度；如果没有这一行，CA13 会只靠静态源码误判。
        openharness_ok, special_details = _alignment_phase148c_gate(repo_root)  # 新增代码+ClaudeCodeAlignmentMatrix：用最终成熟度 evidence 计算 CA13；如果没有这一行，fresh benchmark 结果不会进入矩阵。
    if special_gate == "visible_terminal_gate":  # 新增代码+ClaudeCodeAlignmentMatrix：处理最终可见终端特殊维度；如果没有这一行，CA14 无法从外部 gate 降级或升级。
        status, special_details = _alignment_visible_terminal_gate(repo_root, visible_terminal_gate, final_visible_run_dir)  # 新增代码+ClaudeCodeAlignmentMatrix：计算 CA14 状态和细节；如果没有这一行，最终 gate 不能单独约束 parity。
        return {**dimension, "status": status, "claudecode_ok": claudecode_ok, "openharness_ok": status == "aligned", "details": special_details}  # 新增代码+ClaudeCodeAlignmentMatrix：直接返回 CA14 结果；如果没有这一行，partial 会被普通 missing 逻辑覆盖。
    if claudecode_ok and openharness_ok:  # 新增代码+ClaudeCodeAlignmentMatrix：判断普通维度完全对齐；如果没有这一行，源码和证据通过时不能标记 aligned。
        status = "aligned"  # 新增代码+ClaudeCodeAlignmentMatrix：把通过维度标记为 aligned；如果没有这一行，统计无法累加通过数。
    elif claudecode_ok or openharness_ok:  # 新增代码+ClaudeCodeAlignmentMatrix：判断只有一侧证据存在的情况；如果没有这一行，部分证据无法和完全缺失区分。
        status = "partial"  # 新增代码+ClaudeCodeAlignmentMatrix：把单侧证据标记为 partial；如果没有这一行，待补项会被错误归类。
    else:  # 新增代码+ClaudeCodeAlignmentMatrix：处理两侧证据都不成立的情况；如果没有这一行，严重缺口没有兜底分支。
        status = "missing"  # 新增代码+ClaudeCodeAlignmentMatrix：把缺口标记为 missing；如果没有这一行，统计无法发现严重缺失。
    return {**dimension, "status": status, "claudecode_ok": claudecode_ok, "openharness_ok": openharness_ok, "details": special_details}  # 新增代码+ClaudeCodeAlignmentMatrix：返回单维度完整报告；如果没有这一行，主评估函数拿不到结果。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，_alignment_dimension_status 到此结束；如果没有这个边界说明，用户不容易看出单项评分边界。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，evaluate_claudecode_alignment_matrix 生成完整矩阵；如果没有这段函数，测试和 CLI 没有核心判定入口。
def evaluate_claudecode_alignment_matrix(repo_root: str | Path, claudecode_root: str | Path, *, visible_terminal_gate: bool = False, final_visible_run_dir: str = "") -> dict[str, Any]:  # 新增代码+ClaudeCodeAlignmentMatrix：声明矩阵评估公开 API；如果没有这一行，外部无法传入不同根目录复验。
    dimensions = get_claudecode_alignment_dimensions()  # 新增代码+ClaudeCodeAlignmentMatrix：读取固定 14 项定义；如果没有这一行，后续没有评估对象。
    evaluated = [_alignment_dimension_status(dimension, repo_root, claudecode_root, visible_terminal_gate, final_visible_run_dir) for dimension in dimensions]  # 新增代码+ClaudeCodeAlignmentMatrix：逐项评估所有维度；如果没有这一行，矩阵没有逐项状态。
    aligned_count = len([item for item in evaluated if item.get("status") == "aligned"])  # 新增代码+ClaudeCodeAlignmentMatrix：统计 aligned 数量；如果没有这一行，摘要无法表达完成度。
    partial_count = len([item for item in evaluated if item.get("status") == "partial"])  # 新增代码+ClaudeCodeAlignmentMatrix：统计 partial 数量；如果没有这一行，缺最终 gate 等待项不可见。
    missing_count = len([item for item in evaluated if item.get("status") == "missing"])  # 新增代码+ClaudeCodeAlignmentMatrix：统计 missing 数量；如果没有这一行，严重缺口不可见。
    dimension_total = len(evaluated)  # 新增代码+ClaudeCodeAlignmentMatrix：记录维度总数；如果没有这一行，aligned_count 没有分母。
    if missing_count:  # 新增代码+ClaudeCodeAlignmentMatrix：优先处理严重缺口；如果没有这一行，缺能力时可能仍被误升 partial 或 parity。
        level = CLAUDECODE_ALIGNMENT_MISSING  # 新增代码+ClaudeCodeAlignmentMatrix：设置 missing 等级；如果没有这一行，严重缺口等级不明确。
    elif partial_count:  # 新增代码+ClaudeCodeAlignmentMatrix：处理部分对齐状态；如果没有这一行，缺最终 gate 时可能跳到 parity。
        level = CLAUDECODE_ALIGNMENT_PARTIAL  # 新增代码+ClaudeCodeAlignmentMatrix：设置 partial 等级；如果没有这一行，开发中验收边界不清楚。
    else:  # 新增代码+ClaudeCodeAlignmentMatrix：处理所有维度 aligned 的状态；如果没有这一行，成功路径没有等级。
        level = CLAUDECODE_PARITY  # 新增代码+ClaudeCodeAlignmentMatrix：设置 parity 等级；如果没有这一行，14/14 后没有稳定结论。
    claudecode_parity = level in {CLAUDECODE_PARITY, CLAUDECODE_PARITY_OR_BETTER}  # 新增代码+ClaudeCodeAlignmentMatrix：把等级转成布尔 parity；如果没有这一行，最终成熟度判定器难以消费。
    claudecode_parity_or_better = level == CLAUDECODE_PARITY_OR_BETTER  # 新增代码+ClaudeCodeAlignmentMatrix：单独表达是否超过 ClaudeCode；如果没有这一行，不能区分“对齐”和“超过”。
    return {"marker": COMPUTER_USE_CLAUDECODE_ALIGNMENT_MARKER, "model": "computer_use_claudecode_alignment_matrix", "level": level, "dimension_total": dimension_total, "aligned_count": aligned_count, "partial_count": partial_count, "missing_count": missing_count, "visible_terminal_gate": bool(visible_terminal_gate), "final_visible_run_dir": str(final_visible_run_dir or ""), "claudecode_parity": claudecode_parity, "claudecode_parity_or_better": claudecode_parity_or_better, "excluded_platform_differences": dict(EXCLUDED_PLATFORM_DIFFERENCES), "dimensions": evaluated}  # 修改代码+AlignmentMatrixHardening：返回完整结构化报告并附加系统差异说明；如果没有这一行，调用方拿不到矩阵结果和排除边界。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，evaluate_claudecode_alignment_matrix 到此结束；如果没有这个边界说明，用户不容易看出核心判定范围。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，format_claudecode_alignment_summary_line 生成真实终端单行摘要；如果没有这段函数，scenario 需要解析长 JSON。
def format_claudecode_alignment_summary_line(report: dict[str, Any]) -> str:  # 新增代码+ClaudeCodeAlignmentMatrix：声明摘要格式化公开 API；如果没有这一行，测试无法复用同一输出格式。
    return " ".join([str(report.get("marker", COMPUTER_USE_CLAUDECODE_ALIGNMENT_MARKER)), f"level={report.get('level', CLAUDECODE_ALIGNMENT_MISSING)}", f"aligned={int(report.get('aligned_count', 0) or 0)}/{int(report.get('dimension_total', 0) or 0)}", f"partial={int(report.get('partial_count', 0) or 0)}", f"missing={int(report.get('missing_count', 0) or 0)}", f"visible_terminal_gate={_alignment_bool_token(report.get('visible_terminal_gate'))}", f"claudecode_parity={_alignment_bool_token(report.get('claudecode_parity'))}", f"claudecode_parity_or_better={_alignment_bool_token(report.get('claudecode_parity_or_better'))}"])  # 新增代码+ClaudeCodeAlignmentMatrix：拼出固定顺序 token；如果没有这一行，真实终端验收容易因为格式漂移失败。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，format_claudecode_alignment_summary_line 到此结束；如果没有这个边界说明，用户不容易看出终端摘要范围。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，render_claudecode_alignment_report 生成 Markdown 报告；如果没有这段函数，用户只能读机器 JSON。
def render_claudecode_alignment_report(report: dict[str, Any]) -> str:  # 新增代码+ClaudeCodeAlignmentMatrix：声明报告渲染公开 API；如果没有这一行，write_outputs 无法生成可读文档。
    lines = ["# Computer Use ClaudeCode Alignment Matrix", "", f"- level={report.get('level', CLAUDECODE_ALIGNMENT_MISSING)}", f"- aligned={int(report.get('aligned_count', 0) or 0)}/{int(report.get('dimension_total', 0) or 0)}", f"- partial={int(report.get('partial_count', 0) or 0)}", f"- missing={int(report.get('missing_count', 0) or 0)}", f"- visible_terminal_gate={_alignment_bool_token(report.get('visible_terminal_gate'))}", f"- claudecode_parity={_alignment_bool_token(report.get('claudecode_parity'))}", f"- claudecode_parity_or_better={_alignment_bool_token(report.get('claudecode_parity_or_better'))}", "", "## Dimensions"]  # 新增代码+ClaudeCodeAlignmentMatrix：写入报告头和摘要；如果没有这一行，报告缺少核心结论。
    for item in report.get("dimensions", []):  # 新增代码+ClaudeCodeAlignmentMatrix：遍历维度写明逐项状态；如果没有这一行，用户看不到哪个 gate 卡住。
        if isinstance(item, dict):  # 新增代码+ClaudeCodeAlignmentMatrix：只渲染合法字典项；如果没有这一行，坏数据会让报告崩溃。
            lines.append(f"- {item.get('id', '')} `{item.get('status', '')}` {item.get('name', '')}")  # 新增代码+ClaudeCodeAlignmentMatrix：写入单维度摘要；如果没有这一行，报告无法逐项审计。
    lines.extend(["", "## Excluded Platform Differences"])  # 新增代码+AlignmentMatrixHardening：新增系统差异说明章节；如果没有这行代码，人类报告无法解释哪些内容不计入缺口。
    for key, reason in dict(report.get("excluded_platform_differences", {})).items():  # 新增代码+AlignmentMatrixHardening：遍历系统差异排除项；如果没有这行代码，报告不会列出具体排除原因。
        lines.append(f"- `{key}`: {reason}")  # 新增代码+AlignmentMatrixHardening：写入单个排除项说明；如果没有这行代码，用户无法区分 macOS 差异和真实缺口。
    lines.extend(["", "## Evidence", f"- manifest={ALIGNMENT_MANIFEST}", f"- final_visible_run_dir={report.get('final_visible_run_dir', '')}", ""])  # 新增代码+ClaudeCodeAlignmentMatrix：写入证据路径；如果没有这一行，后续复验不知道看哪里。
    return "\n".join(lines)  # 新增代码+ClaudeCodeAlignmentMatrix：返回 Markdown 文本；如果没有这一行，调用方拿不到可写入内容。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，render_claudecode_alignment_report 到此结束；如果没有这个边界说明，用户不容易看出报告生成范围。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，_alignment_scenario_payload 构造真实可见终端 scenario；如果没有这段函数，矩阵没有规则十七专用验收入口。
def _alignment_scenario_payload() -> dict[str, Any]:  # 新增代码+ClaudeCodeAlignmentMatrix：声明 scenario 结构构造函数；如果没有这一行，write_outputs 要内联复杂 JSON。
    summary_line = f"{COMPUTER_USE_CLAUDECODE_ALIGNMENT_MARKER} level={CLAUDECODE_ALIGNMENT_PARTIAL} aligned=13/14 partial=1 missing=0 visible_terminal_gate=false claudecode_parity=false claudecode_parity_or_better=false"  # 新增代码+ClaudeCodeAlignmentMatrix：定义无最终 gate 时 agent 应复制的稳定摘要；如果没有这一行，场景断言缺少精确目标。
    return {"id": "agent_capability_computer_use_claudecode_alignment_matrix_visible_terminal", "name": "agent_capability_computer_use_claudecode_alignment_matrix_visible_terminal", "output_prefix": "agent_capability_computer_use_claudecode_alignment_matrix_visible_terminal", "window_title_prefix": "LearningAgent-ClaudeCodeAlignment", "entrypoint": "learning_agent/start_oauth_agent.bat", "visible_terminal_gate": True, "screenshot_artifacts_required": True, "max_seconds": 900, "final_log_wait_seconds": 60, "post_success_wait_seconds": 6, "success_marker": COMPUTER_USE_CLAUDECODE_ALIGNMENT_MARKER, "prompt": "Please run the Computer Use ClaudeCode alignment matrix acceptance.", "prompt_lines": ["Please run the Computer Use ClaudeCode alignment matrix. Use only local OpenHarness evidence and the local ClaudeCode source at D:\\ClaudeCode-main\\ClaudeCode-main. Do not open browsers, login windows, passwords, system settings, registry, installers, payment pages, or user documents. The final answer must include the fixed marker: COMPUTER_USE_CLAUDECODE_ALIGNMENT_READY.", "You must call the terminal tool and run this verification command exactly: $env:PYTHONPATH='..'; python -m learning_agent.computer_use_mcp_v2.windows_runtime.claudecode_alignment_matrix --repo-root .. --claudecode-root D:\\ClaudeCode-main\\ClaudeCode-main", f"Do not write the final answer early. Only after the terminal command prints {COMPUTER_USE_CLAUDECODE_ALIGNMENT_MARKER}, the final answer's last line must completely copy: {summary_line}"], "required_event_states": ["agent_ready_for_user_prompt", "user_prompt_received", "final_answer_printed"], "debug_log_contains": [COMPUTER_USE_CLAUDECODE_ALIGNMENT_MARKER, f"level={CLAUDECODE_ALIGNMENT_PARTIAL}", "aligned=13/14", "partial=1", "missing=0", "visible_terminal_gate=false", "claudecode_parity=false", "claudecode_parity_or_better=false"], "event_answer_contains": [COMPUTER_USE_CLAUDECODE_ALIGNMENT_MARKER, f"level={CLAUDECODE_ALIGNMENT_PARTIAL}", "aligned=13/14", "partial=1", "missing=0", "visible_terminal_gate=false", "claudecode_parity=false", "claudecode_parity_or_better=false"], "assertions": {"output_contains": [COMPUTER_USE_CLAUDECODE_ALIGNMENT_MARKER, f"level={CLAUDECODE_ALIGNMENT_PARTIAL}", "aligned=13/14", "partial=1", "missing=0", "visible_terminal_gate=false", "claudecode_parity=false", "claudecode_parity_or_better=false"]}, "max_permission_sent_count": 0}  # 新增代码+ClaudeCodeAlignmentMatrix：返回完整场景 JSON；如果没有这一行，controller 无法启动真实可见终端验收。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，_alignment_scenario_payload 到此结束；如果没有这个边界说明，用户不容易看出 scenario 合同范围。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，write_claudecode_alignment_outputs 写入矩阵产物；如果没有这段函数，评估结果无法被后续 agent 复用。
def write_claudecode_alignment_outputs(repo_root: str | Path, claudecode_root: str | Path, *, visible_terminal_gate: bool = False, final_visible_run_dir: str = "") -> dict[str, str]:  # 新增代码+ClaudeCodeAlignmentMatrix：声明输出写入公开 API；如果没有这一行，测试和 CLI 无法统一落盘。
    root = Path(repo_root)  # 新增代码+ClaudeCodeAlignmentMatrix：规范化仓库根目录；如果没有这一行，后续路径拼接会依赖输入类型。
    report = evaluate_claudecode_alignment_matrix(root, claudecode_root, visible_terminal_gate=visible_terminal_gate, final_visible_run_dir=final_visible_run_dir)  # 新增代码+ClaudeCodeAlignmentMatrix：先生成矩阵报告；如果没有这一行，文件没有内容来源。
    manifest_path = root / ALIGNMENT_MANIFEST  # 新增代码+ClaudeCodeAlignmentMatrix：定位 manifest 输出文件；如果没有这一行，机器证据无法落盘。
    report_path = root / ALIGNMENT_REPORT  # 新增代码+ClaudeCodeAlignmentMatrix：定位 Markdown 报告文件；如果没有这一行，人类报告无法落盘。
    scenario_path = root / ALIGNMENT_SCENARIO  # 新增代码+ClaudeCodeAlignmentMatrix：定位 scenario 文件；如果没有这一行，真实终端验收入口无法落盘。
    manifest_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+ClaudeCodeAlignmentMatrix：确保 manifest 目录存在；如果没有这一行，首次写入会因为缺目录失败。
    report_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+ClaudeCodeAlignmentMatrix：确保报告目录存在；如果没有这一行，首次写入报告会失败。
    scenario_path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+ClaudeCodeAlignmentMatrix：确保 scenario 目录存在；如果没有这一行，验收场景无法写入。
    manifest_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")  # 新增代码+ClaudeCodeAlignmentMatrix：写入机器可读 manifest；如果没有这一行，后续成熟度判定器没有证据输入。
    report_path.write_text(render_claudecode_alignment_report(report), encoding="utf-8")  # 新增代码+ClaudeCodeAlignmentMatrix：写入人类可读报告；如果没有这一行，用户看不到矩阵判定。
    scenario_path.write_text(json.dumps(_alignment_scenario_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # 新增代码+ClaudeCodeAlignmentMatrix：写入真实可见终端 scenario；如果没有这一行，规则十七验收不能自动复现。
    return {"manifest_path": str(manifest_path), "report_path": str(report_path), "scenario_path": str(scenario_path)}  # 新增代码+ClaudeCodeAlignmentMatrix：返回产物路径；如果没有这一行，测试和 CLI 不知道文件写到哪里。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，write_claudecode_alignment_outputs 到此结束；如果没有这个边界说明，用户不容易看出落盘范围。

# 新增代码+ClaudeCodeAlignmentMatrix：函数段开始，main 提供真实终端可调用 CLI；如果没有这段函数，start_oauth_agent.bat 场景无法运行矩阵。
def main(argv: list[str] | None = None) -> int:  # 新增代码+ClaudeCodeAlignmentMatrix：声明 CLI 主入口；如果没有这一行，python -m 无法稳定调用。
    parser = argparse.ArgumentParser(description="Evaluate Computer Use ClaudeCode alignment matrix.")  # 新增代码+ClaudeCodeAlignmentMatrix：创建参数解析器；如果没有这一行，参数错误时没有清楚提示。
    parser.add_argument("--repo-root", default=".")  # 新增代码+ClaudeCodeAlignmentMatrix：支持传入 OpenHarness 根目录；如果没有这一行，真实终端 cwd 改变时找不到证据。
    parser.add_argument("--claudecode-root", default="D:/ClaudeCode-main/ClaudeCode-main")  # 新增代码+ClaudeCodeAlignmentMatrix：支持传入 ClaudeCode 源码目录；如果没有这一行，参照源码位置无法配置。
    parser.add_argument("--visible-terminal-gate", action="store_true")  # 新增代码+ClaudeCodeAlignmentMatrix：允许最终验收后回填可见终端 gate；如果没有这一行，矩阵无法从 partial 晋升 parity。
    parser.add_argument("--final-visible-run-dir", default="")  # 新增代码+ClaudeCodeAlignmentMatrix：允许记录最终可见终端 run 目录；如果没有这一行，parity 证据不可追溯。
    args = parser.parse_args(argv)  # 新增代码+ClaudeCodeAlignmentMatrix：解析命令行参数；如果没有这一行，后续拿不到用户输入。
    outputs = write_claudecode_alignment_outputs(args.repo_root, args.claudecode_root, visible_terminal_gate=args.visible_terminal_gate, final_visible_run_dir=args.final_visible_run_dir)  # 新增代码+ClaudeCodeAlignmentMatrix：写入矩阵产物；如果没有这一行，CLI 只会打印临时结果。
    manifest = _alignment_load_json_file(args.repo_root, ALIGNMENT_MANIFEST)  # 新增代码+ClaudeCodeAlignmentMatrix：重新读取落盘 manifest；如果没有这一行，CLI 输出不能证明文件可读。
    print(format_claudecode_alignment_summary_line(manifest))  # 新增代码+ClaudeCodeAlignmentMatrix：打印稳定单行摘要；如果没有这一行，acceptance controller 找不到固定结论。
    print(f"manifest_path={outputs['manifest_path']}")  # 新增代码+ClaudeCodeAlignmentMatrix：打印 manifest 路径；如果没有这一行，用户不容易定位机器证据。
    print(f"report_path={outputs['report_path']}")  # 新增代码+ClaudeCodeAlignmentMatrix：打印报告路径；如果没有这一行，用户不容易定位可读报告。
    print(f"scenario_path={outputs['scenario_path']}")  # 新增代码+ClaudeCodeAlignmentMatrix：打印 scenario 路径；如果没有这一行，用户不容易定位真实终端入口。
    return 0  # 新增代码+ClaudeCodeAlignmentMatrix：CLI 生成矩阵即返回成功；如果没有这一行，partial 状态会被误当成命令执行失败。
# 新增代码+ClaudeCodeAlignmentMatrix：函数段结束，main 到此结束；如果没有这个边界说明，用户不容易看出 CLI 范围。

__all__ = ["COMPUTER_USE_CLAUDECODE_ALIGNMENT_MARKER", "EXCLUDED_PLATFORM_DIFFERENCES", "evaluate_claudecode_alignment_matrix", "format_claudecode_alignment_summary_line", "get_claudecode_alignment_dimensions", "render_claudecode_alignment_report", "write_claudecode_alignment_outputs"]  # 修改代码+AlignmentMatrixHardening：声明稳定公开 API 并暴露排除项常量；如果没有这一行，后续模块不清楚哪些名称可以依赖。

if __name__ == "__main__":  # 新增代码+ClaudeCodeAlignmentMatrix：模块直接运行入口开始；如果没有这一行，python -m 不会执行 main。
    raise SystemExit(main())  # 新增代码+ClaudeCodeAlignmentMatrix：把 main 返回值转成进程退出码；如果没有这一行，真实终端不会启动矩阵 CLI。
# 新增代码+ClaudeCodeAlignmentMatrix：模块直接运行入口结束，本文件到此结束；如果没有这个边界说明，初学者不容易看出执行逻辑结束位置。
