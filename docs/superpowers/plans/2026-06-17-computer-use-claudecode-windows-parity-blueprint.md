# Computer Use ClaudeCode Windows Parity Blueprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在排除外部 MCP 包内部实现、macOS 专属机制和 Windows/macOS 系统差异后，让 OpenHarness 的 agent Computer Use 功能在协议、权限、剪贴板、真实输入证据、总链路验收上尽可能对齐 ClaudeCode 的可观察行为。

**Architecture:** 保留 OpenHarness 现有 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp` 作为 ClaudeCode-compatible 工具外观层，不推倒 Windows 后端；在 Windows 运行时补齐真实系统剪贴板桥接、权限审批语义的可见性、真实 SendInput/GUI 证据和可见终端门禁。所有对齐都通过测试、矩阵和真实终端场景验证，不用“代码看起来像”替代“链路真的能跑”。

**Tech Stack:** Python 3、`unittest`、CodeGraph、Windows Win32/User32/Clipboard API via `ctypes`、现有 `learning_agent/computer_use_mcp_v2`、现有 `learning_agent/acceptance_controller`、`H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`。

---

## 0. 固定范围与结论

这份蓝图只覆盖值得继续对齐的主要差异。当前已知基线来自对 OpenHarness 与 `D:\ClaudeCode-main\ClaudeCode-main` 的 CodeGraph/源码对比和矩阵运行：

```powershell
python -m learning_agent.computer_use_mcp_v2.windows_runtime.claudecode_alignment_matrix --repo-root . --claudecode-root D:\ClaudeCode-main\ClaudeCode-main
```

当前基线结果：

```text
COMPUTER_USE_CLAUDECODE_ALIGNMENT_READY level=CLAUDECODE_ALIGNMENT_PARTIAL aligned=11/14 partial=3 missing=0 visible_terminal_gate=false claudecode_parity=false claudecode_parity_or_better=false
```

主要待对齐点：

- CA07：真实 Windows 输入链路和证据需要更稳地证明，而不是只证明文件存在。
- CA13：真实 GUI benchmark/成熟度证据需要更明确地绑定到 ClaudeCode 对齐矩阵。
- CA14：真实可见终端门禁未完成，不能声明完全对齐。
- 剪贴板：ClaudeCode macOS 侧使用真实系统剪贴板的 save/write/verify/paste/restore 语义；OpenHarness v2 当前 `read_clipboard/write_clipboard` 仍以 context 内存文本为主，需要 Windows 系统剪贴板桥接。
- 权限 UI/语义：OpenHarness 已有 `apps/grantFlags/sentinelWarnings` 基础结构，后续应补强审批提示、审计、拒绝路径和测试，而不是重写整套权限系统。

明确不做：

- 不复制外部 `@anthropic-ai/computer-use` 或其他外部 MCP 包内部实现。
- 不实现 macOS TCC、Swift helper、`pbcopy/pbpaste` 原生命令；Windows 侧用等价的 Win32/Clipboard/SendInput 能力。
- 不为了“看起来一样”删除 OpenHarness 已经更适合 Windows 的安全门禁。
- 不一次性重写旧 `learning_agent/computer_use` 与新 `learning_agent/computer_use_mcp_v2` 的全部适配层。
- 不让 Computer Use 自动操作用户登录页、密码管理器、真实支付页面、系统设置、用户私有文档。

## 1. 成功标准

功能成功标准：

- `mcp__computer-use__read_clipboard` 在授权允许时读取 Windows 系统剪贴板文本，返回中包含 `backend="windows_system_clipboard"` 或等价字段。
- `mcp__computer-use__write_clipboard` 在授权允许时写入 Windows 系统剪贴板文本，随后 `read_clipboard` 能读回同一文本。
- `grantFlags` 关闭剪贴板读写时，剪贴板工具返回权限拒绝，不触碰系统剪贴板。
- 需要“输入大量文本”的路径如果使用剪贴板辅助输入，必须执行 save/write/verify/paste/restore，结束后恢复用户原剪贴板。
- `request_access` 的用户审批提示能看见 `apps`、旧字段兼容 `applications`、`grantFlags`、`sentinelWarnings`、申请原因、拒绝结果。
- CA07、CA13、CA14 三项的矩阵判定来源清晰，可通过可复验的证据文件或可见终端验收目录证明。
- 最终回答前，如果执行了功能修改，必须完成 AGENTS 规则十七要求的真实可见终端交互验收；做不到时只能说“真实可见终端交互验收未完成，不能声明开发完成。”

文档与防跑偏标准：

- 每轮执行前先确认本蓝图的当前任务编号。
- 每完成一个任务，更新 `agent_memory/progress.md`。
- 发现真实 bug 时，简单 bug 直接修；复杂 bug 先写入 `agent_memory/bugs.md` 并给治本方案。
- 所有新写或修改的代码，执行阶段必须按 AGENTS.md 给每行新增/修改代码补中文注释，并把新增/修改代码另存到 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\test`。

## 2. 文件结构

计划创建或修改的文件：

- Create: `learning_agent/computer_use_mcp_v2/windows_runtime/system_clipboard.py`
  - 责任：封装 Windows 系统剪贴板读写；提供真实后端和内存测试后端；不混入工具协议。
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`
  - 责任：给 `ComputerUseMcpV2Context` 增加剪贴板后端字段和剪贴板权限检查入口。
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`
  - 责任：绑定默认 Windows 剪贴板后端；测试可注入内存后端。
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/clipboard.py`
  - 责任：从 context-only 剪贴板切换为“授权检查 + 后端读写 + 明确 fallback”。
- Create: `learning_agent/tests/test_computer_use_mcp_v2_clipboard_system_bridge.py`
  - 责任：覆盖授权成功、授权拒绝、读写一致、后端失败返回。
- Create: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_prompt.py`
  - 责任：集中生成 `request_access` 的审批提示文本，避免 JSON 字符串散落在权限函数里。
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py`
  - 责任：复用审批提示构造器，补强拒绝 payload、审计字段和兼容字段。
- Create: `learning_agent/tests/test_computer_use_mcp_v2_permission_approval_prompt.py`
  - 责任：覆盖 `apps/grantFlags/sentinelWarnings/reason` 和拒绝结果。
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/claudecode_alignment_matrix.py`
  - 责任：让 CA07/CA13/CA14 的判定只依赖可复验事实，并把排除项单独标识。
- Create or Modify: `learning_agent/tests/test_computer_use_mcp_v2_claudecode_alignment_matrix.py`
  - 责任：覆盖矩阵 partial/parity 判定，避免未来误报。
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_claudecode_windows_parity_visible_terminal.json`
  - 责任：定义安全的可见终端验收 prompt 和成功 token。
- Modify: `agent_memory/context.md`
  - 责任：记录 ClaudeCode Windows parity 的范围边界。
- Modify: `agent_memory/progress.md`
  - 责任：记录每个任务状态和下一步。
- Modify: `agent_memory/bugs.md`
  - 责任：记录执行中发现的真实问题与风险。
- Create: `learning_agent/test/<next-number-or-task-name>/...`
  - 责任：按 AGENTS.md 另存新增/修改代码和中文注释副本，供用户学习。

## 3. 总链路目标图

```mermaid
flowchart LR
    A["用户真实终端 prompt"] --> B["agent 主循环"]
    B --> C["agent_adapter 拦截 mcp__computer-use__*"]
    C --> D["computer_use_mcp_v2 runtime dispatch"]
    D --> E["inferred_ant_mcp 工具外观"]
    E --> F["request_access 权限审批"]
    F --> G["Windows 后端: observe / screenshot / SendInput / clipboard"]
    G --> H["trace + evidence + alignment matrix"]
    H --> I["真实可见终端验收结果"]
```

这个图是后续执行的防跑偏总线。任何新增代码都必须能说明自己接在图中的哪一段，否则先暂停讨论。

---

## Task 1: Baseline Freeze And Evidence Map

**Files:**
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/context.md`
- Read with CodeGraph: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/clipboard.py`
- Read with CodeGraph: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py`
- Read with CodeGraph: `learning_agent/computer_use_mcp_v2/windows_runtime/claudecode_alignment_matrix.py`

- [ ] **Step 1: 记录本次对齐范围**

把以下内容追加到 `agent_memory/context.md`：

```markdown
## Computer Use ClaudeCode Windows Parity Scope - 2026-06-17

- 目标：让 OpenHarness Computer Use 在 Windows 上对齐 ClaudeCode 的可观察协议、权限、剪贴板、真实输入证据和可见终端验收。
- 排除：外部 MCP 包内部实现、macOS TCC、Swift helper、macOS `pbcopy/pbpaste`、Windows/macOS 系统差异导致的不可比行为。
- 当前矩阵基线：11/14 aligned，CA07/CA13/CA14 为 partial，CA14 的 visible terminal gate 为 false。
- 优先级：先补真实系统剪贴板和权限语义测试，再补矩阵证据和真实可见终端验收。
```

- [ ] **Step 2: 记录当前任务入口**

把以下内容追加到 `agent_memory/progress.md`：

```markdown
## 2026-06-17 Computer Use ClaudeCode Windows Parity Blueprint

- 当前任务：按 `docs/superpowers/plans/2026-06-17-computer-use-claudecode-windows-parity-blueprint.md` 执行。
- 下一步：Task 1 冻结基线，Task 2 先写剪贴板桥接失败测试。
- 停止条件：真实系统剪贴板触及敏感内容、真实 GUI benchmark 需要操作用户私有数据、或可见终端无法人工确认。
```

- [ ] **Step 3: 运行当前矩阵，确认没有误读**

Run:

```powershell
python -m learning_agent.computer_use_mcp_v2.windows_runtime.claudecode_alignment_matrix --repo-root . --claudecode-root D:\ClaudeCode-main\ClaudeCode-main
```

Expected:

```text
COMPUTER_USE_CLAUDECODE_ALIGNMENT_READY
```

并确认输出仍然能看到：

```text
visible_terminal_gate=false
```

- [ ] **Step 4: 查询 CodeGraph，冻结相关源文件位置**

Run:

```powershell
codegraph explore "computer use clipboard request_access permissions alignment matrix visible terminal grantFlags WindowsProductionClipboardGuard"
```

Expected:

```text
Exploration:
```

记录到 `agent_memory/progress.md`：

```markdown
- CodeGraph 已确认：clipboard.py 当前以 context clipboard 为主；permissions.py 已有 apps/grantFlags/sentinelWarnings；claudecode_alignment_matrix.py 当前 CA07/CA13/CA14 仍需补证据和门禁。
```

- [ ] **Step 5: Commit**

```powershell
git add agent_memory/context.md agent_memory/progress.md
git commit -m "docs: freeze computer use claudecode windows parity baseline"
```

## Task 2: Windows System Clipboard Bridge

**Files:**
- Create: `learning_agent/tests/test_computer_use_mcp_v2_clipboard_system_bridge.py`
- Create: `learning_agent/computer_use_mcp_v2/windows_runtime/system_clipboard.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/clipboard.py`
- Create: `learning_agent/test/<next-folder>/computer_use_clipboard_system_bridge.py`

- [ ] **Step 1: 写失败测试，证明当前 context-only 剪贴板不够对齐**

在 `learning_agent/tests/test_computer_use_mcp_v2_clipboard_system_bridge.py` 写入测试。测试里的内存后端模拟 Windows 系统剪贴板，这样自动化测试不污染用户真实剪贴板：

```python
from __future__ import annotations

import unittest

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.clipboard import read_clipboard, write_clipboard
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context
from learning_agent.computer_use_mcp_v2.windows_runtime.system_clipboard import MemoryClipboardBackend


class ComputerUseMcpV2ClipboardSystemBridgeTests(unittest.TestCase):
    def test_write_then_read_uses_bound_clipboard_backend(self) -> None:
        backend = MemoryClipboardBackend(initial_text="")
        context = ComputerUseMcpV2Context(clipboard_backend=backend)
        context.grant_flags["clipboardRead"] = True
        context.grant_flags["clipboardWrite"] = True

        write_result = write_clipboard(context, "ClaudeCode parity text")
        read_result = read_clipboard(context)

        self.assertEqual(write_result["type"], "tool_result")
        self.assertEqual(write_result["payload"]["backend"], "memory_system_clipboard")
        self.assertEqual(read_result["payload"]["text"], "ClaudeCode parity text")
        self.assertEqual(read_result["payload"]["backend"], "memory_system_clipboard")

    def test_read_clipboard_requires_grant_flag(self) -> None:
        backend = MemoryClipboardBackend(initial_text="secret from test")
        context = ComputerUseMcpV2Context(clipboard_backend=backend)
        context.grant_flags["clipboardRead"] = False

        result = read_clipboard(context)

        self.assertEqual(result["type"], "tool_error")
        self.assertEqual(result["error_class"], "permission_denied")
        self.assertEqual(backend.read_count, 0)

    def test_write_clipboard_requires_grant_flag(self) -> None:
        backend = MemoryClipboardBackend(initial_text="original")
        context = ComputerUseMcpV2Context(clipboard_backend=backend)
        context.grant_flags["clipboardWrite"] = False

        result = write_clipboard(context, "blocked")

        self.assertEqual(result["type"], "tool_error")
        self.assertEqual(result["error_class"], "permission_denied")
        self.assertEqual(backend.text, "original")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认先失败**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_clipboard_system_bridge
```

Expected:

```text
FAILED
```

失败原因应指向 `system_clipboard` 模块不存在、`ComputerUseMcpV2Context` 没有 `clipboard_backend`，或返回 backend 仍是 context-only。

- [ ] **Step 3: 新增 Windows 剪贴板后端**

在 `learning_agent/computer_use_mcp_v2/windows_runtime/system_clipboard.py` 创建后端。执行阶段必须给每行新增代码补 AGENTS.md 要求的中文注释；下面是实现结构和接口合同：

```python
from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Protocol


class ClipboardBackend(Protocol):
    backend_name: str

    def read_text(self) -> str:
        ...

    def write_text(self, text: str) -> None:
        ...


class MemoryClipboardBackend:
    backend_name = "memory_system_clipboard"

    def __init__(self, initial_text: str = "") -> None:
        self.text = initial_text
        self.read_count = 0
        self.write_count = 0

    def read_text(self) -> str:
        self.read_count += 1
        return self.text

    def write_text(self, text: str) -> None:
        self.write_count += 1
        self.text = str(text)


class WindowsClipboardBackend:
    backend_name = "windows_system_clipboard"

    def read_text(self) -> str:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.OpenClipboard(None):
            raise RuntimeError("open_clipboard_failed")
        try:
            handle = user32.GetClipboardData(13)
            if not handle:
                return ""
            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                raise RuntimeError("global_lock_failed")
            try:
                return ctypes.wstring_at(pointer)
            finally:
                kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()

    def write_text(self, text: str) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        data = str(text)
        if not user32.OpenClipboard(None):
            raise RuntimeError("open_clipboard_failed")
        try:
            if not user32.EmptyClipboard():
                raise RuntimeError("empty_clipboard_failed")
            encoded = data + "\0"
            byte_count = len(encoded) * ctypes.sizeof(wintypes.WCHAR)
            handle = kernel32.GlobalAlloc(0x0002, byte_count)
            if not handle:
                raise RuntimeError("global_alloc_failed")
            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                kernel32.GlobalFree(handle)
                raise RuntimeError("global_lock_failed")
            try:
                ctypes.memmove(pointer, ctypes.create_unicode_buffer(encoded), byte_count)
            finally:
                kernel32.GlobalUnlock(handle)
            if not user32.SetClipboardData(13, handle):
                kernel32.GlobalFree(handle)
                raise RuntimeError("set_clipboard_data_failed")
        finally:
            user32.CloseClipboard()
```

- [ ] **Step 4: 给 context 增加剪贴板后端字段**

在 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py` 的 `ComputerUseMcpV2Context` 增加字段。执行时每行按 AGENTS.md 加中文注释：

```python
clipboard_backend: ClipboardBackend | None = None
```

如果现有文件不适合直接引用 `ClipboardBackend`，使用 `Any` 并在 `clipboard.py` 做运行时检查，避免循环导入。

- [ ] **Step 5: 绑定默认后端**

在 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py` 创建或绑定上下文时设置：

```python
from learning_agent.computer_use_mcp_v2.windows_runtime.system_clipboard import WindowsClipboardBackend

if context.clipboard_backend is None:
    context.clipboard_backend = WindowsClipboardBackend()
```

自动化测试仍通过构造 `ComputerUseMcpV2Context(clipboard_backend=MemoryClipboardBackend(...))` 注入内存后端。

- [ ] **Step 6: 修改 clipboard 工具**

在 `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/clipboard.py` 中执行以下行为：

```python
def read_clipboard(context: ComputerUseMcpV2Context) -> dict[str, Any]:
    if not context.grant_flags.get("clipboardRead", False):
        return error_result("read_clipboard", "clipboard_read_not_granted", error_class="permission_denied")
    backend = context.clipboard_backend
    if backend is None:
        return error_result("read_clipboard", "clipboard_backend_unavailable", error_class="unavailable")
    text = backend.read_text()
    return success_result("read_clipboard", {"text": text, "text_length": len(text), "backend": backend.backend_name})


def write_clipboard(context: ComputerUseMcpV2Context, text: str) -> dict[str, Any]:
    if not context.grant_flags.get("clipboardWrite", False):
        return error_result("write_clipboard", "clipboard_write_not_granted", error_class="permission_denied")
    backend = context.clipboard_backend
    if backend is None:
        return error_result("write_clipboard", "clipboard_backend_unavailable", error_class="unavailable")
    value = str(text)
    backend.write_text(value)
    return success_result("write_clipboard", {"text_length": len(value), "backend": backend.backend_name})
```

- [ ] **Step 7: 跑剪贴板测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_clipboard_system_bridge
```

Expected:

```text
OK
```

- [ ] **Step 8: 另存学习副本**

把本任务新增或修改的关键代码复制到：

```text
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\test\computer_use_clipboard_system_bridge_20260617\
```

学习副本至少包含：

- `system_clipboard.py`
- `clipboard.py`
- `types.py` 中新增字段片段
- `test_computer_use_mcp_v2_clipboard_system_bridge.py`

- [ ] **Step 9: Commit**

```powershell
git add learning_agent/computer_use_mcp_v2/windows_runtime/system_clipboard.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/types.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/bind_session_context.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/clipboard.py learning_agent/tests/test_computer_use_mcp_v2_clipboard_system_bridge.py learning_agent/test/computer_use_clipboard_system_bridge_20260617
git commit -m "feat: add windows system clipboard bridge for computer use"
```

## Task 3: Clipboard Save Verify Restore Contract

**Files:**
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/system_clipboard.py`
- Create: `learning_agent/tests/test_computer_use_mcp_v2_clipboard_restore_contract.py`
- Modify if needed: `learning_agent/computer_use_mcp_v2/windows_runtime/production_live_control.py`
- Create: `learning_agent/test/<next-folder>/computer_use_clipboard_restore_contract.py`

- [ ] **Step 1: 写失败测试，锁定 save/write/verify/restore**

在 `learning_agent/tests/test_computer_use_mcp_v2_clipboard_restore_contract.py` 写入：

```python
from __future__ import annotations

import unittest

from learning_agent.computer_use_mcp_v2.windows_runtime.system_clipboard import MemoryClipboardBackend, paste_text_with_restore


class ClipboardRestoreContractTests(unittest.TestCase):
    def test_paste_text_with_restore_restores_original_clipboard(self) -> None:
        backend = MemoryClipboardBackend(initial_text="original clipboard")
        pasted: list[str] = []

        result = paste_text_with_restore(backend, "typed through clipboard", lambda: pasted.append(backend.text))

        self.assertTrue(result["restored"])
        self.assertTrue(result["verified_before_paste"])
        self.assertEqual(pasted, ["typed through clipboard"])
        self.assertEqual(backend.text, "original clipboard")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认先失败**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_clipboard_restore_contract
```

Expected:

```text
FAILED
```

- [ ] **Step 3: 实现可复用恢复合同**

在 `system_clipboard.py` 增加：

```python
from collections.abc import Callable
from typing import Any


def paste_text_with_restore(backend: ClipboardBackend, text: str, paste_callback: Callable[[], None]) -> dict[str, Any]:
    original = backend.read_text()
    requested = str(text)
    backend.write_text(requested)
    verified = backend.read_text() == requested
    if not verified:
        backend.write_text(original)
        return {"pasted": False, "verified_before_paste": False, "restored": True, "backend": backend.backend_name}
    try:
        paste_callback()
        return {"pasted": True, "verified_before_paste": True, "restored": False, "backend": backend.backend_name}
    finally:
        backend.write_text(original)
```

执行阶段要把返回值中的 `restored` 设置为真实恢复后的结果；如果 `finally` 恢复失败，返回或抛出的证据必须明确说明恢复失败，不能静默吞掉。

- [ ] **Step 4: 跑恢复合同测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_clipboard_restore_contract
```

Expected:

```text
OK
```

- [ ] **Step 5: 决定是否接入真实输入路径**

用 CodeGraph 查询 `type`、`send_keys`、`text input` 相关路径：

```powershell
codegraph explore "computer use type text SendInput paste clipboard production live control"
```

若现有真实输入路径已经可靠使用 SendInput 文本输入，则本任务只保留恢复合同和测试。

若现有真实输入路径需要通过剪贴板输入长文本，则只在授权满足以下条件时接入：

```text
grantFlags.clipboardRead = true
grantFlags.clipboardWrite = true
grantFlags.clipboardPaste = true
```

- [ ] **Step 6: Commit**

```powershell
git add learning_agent/computer_use_mcp_v2/windows_runtime/system_clipboard.py learning_agent/tests/test_computer_use_mcp_v2_clipboard_restore_contract.py learning_agent/test
git commit -m "feat: add clipboard paste restore contract"
```

## Task 4: Permission Approval Prompt Parity

**Files:**
- Create: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_prompt.py`
- Modify: `learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py`
- Create: `learning_agent/tests/test_computer_use_mcp_v2_permission_approval_prompt.py`
- Create: `learning_agent/test/<next-folder>/computer_use_permission_approval_prompt.py`

- [ ] **Step 1: 写审批提示测试**

在 `learning_agent/tests/test_computer_use_mcp_v2_permission_approval_prompt.py` 写入：

```python
from __future__ import annotations

import unittest

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.approval_prompt import build_computer_use_approval_prompt
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.permissions import request_access
from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.types import ComputerUseMcpV2Context


class ComputerUsePermissionApprovalPromptTests(unittest.TestCase):
    def test_prompt_contains_apps_grant_flags_warnings_and_reason(self) -> None:
        prompt = build_computer_use_approval_prompt(
            apps=[{"displayName": "PowerShell", "bundleId": "powershell.exe"}],
            applications=["PowerShell"],
            grant_flags={"clipboardRead": True, "clipboardWrite": False},
            sentinel_warnings=["shell_application_requested"],
            reason="需要验证安全拒绝路径",
        )

        self.assertIn("PowerShell", prompt)
        self.assertIn("clipboardRead", prompt)
        self.assertIn("clipboardWrite", prompt)
        self.assertIn("shell_application_requested", prompt)
        self.assertIn("需要验证安全拒绝路径", prompt)

    def test_request_access_denied_result_keeps_denied_payload(self) -> None:
        prompts: list[str] = []
        context = ComputerUseMcpV2Context(ask_permission=lambda prompt: prompts.append(prompt) or False)

        result = request_access(
            context,
            {
                "apps": [{"displayName": "PowerShell", "bundleId": "powershell.exe"}],
                "grantFlags": {"clipboardRead": True},
                "reason": "测试拒绝",
            },
        )

        self.assertEqual(result["type"], "tool_error")
        self.assertEqual(result["error_class"], "permission_denied")
        self.assertEqual(result["payload"]["deniedApps"][0]["displayName"], "PowerShell")
        self.assertIn("PowerShell", prompts[0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认先失败或覆盖不足**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_permission_approval_prompt
```

Expected:

```text
FAILED
```

如果当前 `permissions.py` 已经让第二个测试通过，第一个测试仍应因为 `approval_prompt.py` 不存在而失败。

- [ ] **Step 3: 新增审批提示构造器**

在 `approval_prompt.py` 创建：

```python
from __future__ import annotations

import json
from typing import Any


def build_computer_use_approval_prompt(
    apps: list[dict[str, str]],
    applications: list[str],
    grant_flags: dict[str, bool],
    sentinel_warnings: list[str],
    reason: str,
) -> str:
    payload: dict[str, Any] = {
        "apps": apps,
        "applications": applications,
        "grantFlags": grant_flags,
        "sentinelWarnings": sentinel_warnings,
        "reason": reason,
    }
    return "Computer Use v2 请求控制应用：\n" + json.dumps(payload, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 修改 permissions.py 使用构造器**

把 `request_access` 里的手写 prompt 改为：

```python
from .approval_prompt import build_computer_use_approval_prompt

prompt = build_computer_use_approval_prompt(
    apps=apps,
    applications=applications,
    grant_flags=grant_flags,
    sentinel_warnings=sentinel_warnings,
    reason=reason,
)
```

- [ ] **Step 5: 跑权限测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_permission_approval_prompt
```

Expected:

```text
OK
```

- [ ] **Step 6: Commit**

```powershell
git add learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_prompt.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py learning_agent/tests/test_computer_use_mcp_v2_permission_approval_prompt.py learning_agent/test
git commit -m "feat: clarify computer use approval prompt parity"
```

## Task 5: Alignment Matrix CA07 CA13 CA14 Hardening

**Files:**
- Modify: `learning_agent/computer_use_mcp_v2/windows_runtime/claudecode_alignment_matrix.py`
- Create or Modify: `learning_agent/tests/test_computer_use_mcp_v2_claudecode_alignment_matrix.py`
- Modify: `agent_memory/progress.md`

- [ ] **Step 1: 写矩阵测试，锁定 CA07 证据不能只靠文件名**

在矩阵测试文件加入：

```python
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from learning_agent.computer_use_mcp_v2.windows_runtime.claudecode_alignment_matrix import evaluate_claudecode_alignment_matrix


class ClaudeCodeAlignmentMatrixTests(unittest.TestCase):
    def test_matrix_requires_real_sendinput_evidence_content_for_ca07(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            evidence_dir = repo_root / "learning_agent" / "computer_use_mcp_v2" / "windows_runtime"
            evidence_dir.mkdir(parents=True)
            (evidence_dir / "real_sendinput_guard.py").write_text("SendInput\nphysical_dispatch\nreal_sendinput\n", encoding="utf-8")
            (evidence_dir / "sendinput_executor.py").write_text("SendInput\nphysical_dispatch\nreal_sendinput\n", encoding="utf-8")
            (evidence_dir / "phase148c_fresh_benchmark_evidence_20260613.json").write_text(
                '{"fresh_count": 7, "required_count": 7, "failures_fixed": true}',
                encoding="utf-8",
            )

            result = evaluate_claudecode_alignment_matrix(repo_root=repo_root, claudecode_root=repo_root)

            ca07 = [item for item in result["dimensions"] if item["id"] == "CA07"][0]
            self.assertEqual(ca07["status"], "aligned")
```

- [ ] **Step 2: 写矩阵测试，锁定 visible terminal gate**

同一测试文件加入：

```python
    def test_matrix_keeps_ca14_partial_without_visible_terminal_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            runtime_dir = repo_root / "learning_agent" / "computer_use_mcp_v2" / "windows_runtime"
            runtime_dir.mkdir(parents=True)

            result = evaluate_claudecode_alignment_matrix(repo_root=repo_root, claudecode_root=repo_root)

            ca14 = [item for item in result["dimensions"] if item["id"] == "CA14"][0]
            self.assertIn(ca14["status"], {"partial", "missing"})
            self.assertFalse(result["visible_terminal_gate"])
```

- [ ] **Step 3: 运行矩阵测试，确认当前行为**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_alignment_matrix
```

Expected:

```text
OK
```

如果测试失败，先读失败输出，确认是测试期望与当前矩阵结构不一致，还是矩阵真实误报。

- [ ] **Step 4: 修改矩阵排除项表达**

在 `claudecode_alignment_matrix.py` 中给不可比项加 `excluded_reason` 字段，矩阵结果里不把以下内容算作 OpenHarness 缺失：

```python
EXCLUDED_PLATFORM_DIFFERENCES = {
    "macos_tcc": "ClaudeCode macOS TCC 权限不适用于 Windows。",
    "swift_helper": "ClaudeCode Swift helper 是 macOS 原生实现，Windows 使用 Win32/UIA/SendInput 等等价能力。",
    "external_mcp_package_internals": "外部 MCP 包内部代码不属于 OpenHarness 仓库可控范围。",
}
```

保留 CA07/CA13/CA14 为必须通过项，不把它们放入排除项。

- [ ] **Step 5: 运行矩阵命令**

Run:

```powershell
python -m learning_agent.computer_use_mcp_v2.windows_runtime.claudecode_alignment_matrix --repo-root . --claudecode-root D:\ClaudeCode-main\ClaudeCode-main
```

Expected before visible terminal验收:

```text
level=CLAUDECODE_ALIGNMENT_PARTIAL
visible_terminal_gate=false
```

Expected after visible terminal验收:

```text
visible_terminal_gate=true
```

- [ ] **Step 6: Commit**

```powershell
git add learning_agent/computer_use_mcp_v2/windows_runtime/claudecode_alignment_matrix.py learning_agent/tests/test_computer_use_mcp_v2_claudecode_alignment_matrix.py agent_memory/progress.md
git commit -m "test: harden computer use claudecode alignment matrix"
```

## Task 6: Safe Real GUI Evidence Scenario

**Files:**
- Create: `learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_claudecode_windows_parity_visible_terminal.json`
- Modify: `agent_memory/progress.md`
- Modify if needed: `learning_agent/computer_use_mcp_v2/windows_runtime/claudecode_alignment_matrix.py`

- [ ] **Step 1: 新增安全可见终端验收场景**

创建场景文件，内容使用安全 prompt，不要求登录、不碰真实文档、不打开系统设置：

```json
{
  "name": "agent_capability_computer_use_claudecode_windows_parity_visible_terminal",
  "description": "验证 Computer Use ClaudeCode Windows parity 的真实可见终端链路，范围限制在授权、剪贴板、状态查询和安全观察。",
  "start_bat": "H:\\codexworkplace\\sofeware\\OpenHarness-main\\learning_agent\\start_oauth_agent.bat",
  "visible_terminal_required": true,
  "prompt": "请安全验证 Computer Use MCP：先 request_access 申请只读观察和剪贴板读写权限，目标应用只允许 Notepad 或当前安全测试窗口；然后 list_granted_applications；然后 write_clipboard 写入 OPENHARNESS_CLAUDECODE_WINDOWS_PARITY_TEST；再 read_clipboard 读回；不要打开登录页、不要操作用户文件、不要改系统设置。最后只在确认工具成功后输出 COMPUTER_USE_CLAUDECODE_WINDOWS_PARITY_OK。",
  "success_token": "COMPUTER_USE_CLAUDECODE_WINDOWS_PARITY_OK",
  "forbidden_terms": [
    "password",
    "支付",
    "系统设置",
    "用户文档"
  ]
}
```

- [ ] **Step 2: 记录人工验收步骤**

把以下步骤写入 `agent_memory/progress.md`：

```markdown
### Visible terminal acceptance steps

1. 启动 `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat`。
2. 确认它是用户本地电脑上可见的真实终端窗口。
3. 在 agent 交互提示符输入场景 prompt。
4. 观察终端输出是否出现 `COMPUTER_USE_CLAUDECODE_WINDOWS_PARITY_OK`。
5. 只有看到真实终端成功输出，才允许把 CA14 记为通过。
```

- [ ] **Step 3: 执行真实可见终端验收**

Run:

```powershell
Start-Process -FilePath "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\start_oauth_agent.bat"
```

Manual input in visible terminal:

```text
请安全验证 Computer Use MCP：先 request_access 申请只读观察和剪贴板读写权限，目标应用只允许 Notepad 或当前安全测试窗口；然后 list_granted_applications；然后 write_clipboard 写入 OPENHARNESS_CLAUDECODE_WINDOWS_PARITY_TEST；再 read_clipboard 读回；不要打开登录页、不要操作用户文件、不要改系统设置。最后只在确认工具成功后输出 COMPUTER_USE_CLAUDECODE_WINDOWS_PARITY_OK。
```

Expected visible terminal output:

```text
COMPUTER_USE_CLAUDECODE_WINDOWS_PARITY_OK
```

如果当前 Codex 环境无法观察或输入真实可见终端，最终汇报必须写：

```text
真实可见终端交互验收未完成，不能声明开发完成。
```

- [ ] **Step 4: 写入可见终端证据目录**

可见终端成功后，把证据目录写入矩阵可读取的位置，例如：

```text
learning_agent/acceptance_controller/evidence/computer_use_claudecode_windows_parity_visible_terminal_20260617/
```

证据目录至少包含：

- `prompt.txt`
- `terminal_output_excerpt.txt`
- `visible_terminal_gate.json`

`visible_terminal_gate.json` 内容：

```json
{
  "visible_terminal_gate": true,
  "success_token": "COMPUTER_USE_CLAUDECODE_WINDOWS_PARITY_OK",
  "start_bat": "H:\\codexworkplace\\sofeware\\OpenHarness-main\\learning_agent\\start_oauth_agent.bat",
  "completed_at": "2026-06-17",
  "operator_confirmed_visible_terminal": true
}
```

- [ ] **Step 5: Commit**

```powershell
git add learning_agent/acceptance_controller/scenarios/agent_capability_computer_use_claudecode_windows_parity_visible_terminal.json learning_agent/acceptance_controller/evidence agent_memory/progress.md
git commit -m "test: add visible terminal computer use parity scenario"
```

## Task 7: Full Verification Gate

**Files:**
- Modify: `agent_memory/progress.md`
- Modify: `agent_memory/bugs.md` if any issue is found
- Modify: `learning_agent/test/...` learning copies from prior tasks

- [ ] **Step 1: 跑聚焦测试**

Run:

```powershell
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_clipboard_system_bridge
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_clipboard_restore_contract
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_permission_approval_prompt
python -m unittest learning_agent.tests.test_computer_use_mcp_v2_claudecode_alignment_matrix
```

Expected:

```text
OK
OK
OK
OK
```

- [ ] **Step 2: 跑语法检查**

Run:

```powershell
python -m py_compile learning_agent/computer_use_mcp_v2/windows_runtime/system_clipboard.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/clipboard.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/permissions.py learning_agent/computer_use_mcp_v2/inferred_ant_mcp/approval_prompt.py learning_agent/computer_use_mcp_v2/windows_runtime/claudecode_alignment_matrix.py
```

Expected:

```text
No output and exit code 0
```

- [ ] **Step 3: 跑对齐矩阵**

Run:

```powershell
python -m learning_agent.computer_use_mcp_v2.windows_runtime.claudecode_alignment_matrix --repo-root . --claudecode-root D:\ClaudeCode-main\ClaudeCode-main
```

Expected before visible terminal:

```text
claudecode_parity=false
visible_terminal_gate=false
```

Expected after visible terminal:

```text
claudecode_parity=true
visible_terminal_gate=true
```

如果 CA07 或 CA13 仍是 partial，不能进入“完成”状态，需要回到对应任务补证据。

- [ ] **Step 4: 更新 CodeGraph**

Run:

```powershell
codegraph index --force .
codegraph status .
```

Expected:

```text
indexed
```

如果本地 CodeGraph 命令输出不同，只要确认 `.codegraph` 索引更新成功即可。

- [ ] **Step 5: 真实可见终端验收**

必须执行 Task 6 的真实可见终端步骤。自动化测试、CLI prompt、日志、HTTP bridge、selftest 都不能替代。

通过条件：

```text
代码修改完成 + 自动化测试通过 + start_oauth_agent.bat 可见终端交互测试通过
```

- [ ] **Step 6: 记录最终状态**

成功后追加到 `agent_memory/progress.md`：

```markdown
## 2026-06-17 Computer Use ClaudeCode Windows Parity Result

- 剪贴板系统桥接：通过。
- 权限审批提示：通过。
- CA07/CA13/CA14 矩阵门禁：通过。
- 真实可见终端交互验收：通过。
- 结论：OpenHarness Computer Use 在排除外部 MCP 包内部实现和系统差异后，达到 ClaudeCode Windows parity 目标。
```

如果未完成真实可见终端验收，写：

```markdown
## 2026-06-17 Computer Use ClaudeCode Windows Parity Result

- 自动化测试：记录实际结果。
- 矩阵：记录实际结果。
- 真实可见终端交互验收：未完成。
- 结论：不能声明开发完成，等待用户在真实终端输入测试 prompt 并反馈输出或截图。
```

- [ ] **Step 7: Commit**

```powershell
git add agent_memory/progress.md agent_memory/bugs.md learning_agent/test
git commit -m "docs: record computer use parity verification result"
```

## 4. 风险与停止条件

必须停止并汇报的情况：

- Windows 系统剪贴板读取到疑似密码、token、私密文本，不继续打印完整内容。
- 真实 GUI 验收需要操作用户真实账号、支付页面、系统设置、密码管理器、用户私有文档。
- CA07/CA13 证据只能靠“文件存在”证明，无法证明真实 SendInput 或 GUI benchmark 成功。
- 外部 MCP 包内部行为无法从 ClaudeCode 可见源码推断，不能把猜测写成结论。
- 可见终端无法启动、无法观察、无法输入，不能声明开发完成。

治本原则：

- 如果权限语义继续分散在多个文件，优先抽成小型审批提示/权限 payload 模块，而不是在每个工具里拼 JSON。
- 如果矩阵反复误报，优先修矩阵的数据模型和证据读取方式，而不是为单次运行写特殊分支。
- 如果真实输入链路不稳定，优先补可复验的最小 benchmark 和证据结构，而不是扩大可操作应用范围。

## 5. 最终验收清单

- [ ] CodeGraph 已用于定位相关代码。
- [ ] 新增/修改代码每行都有中文注释，并说明没有该行会怎样。
- [ ] 每个新增/修改函数段顶部和结尾都有中文解释。
- [ ] 新增/修改代码已另存到 `learning_agent\test`。
- [ ] `agent_memory/context.md` 已记录范围边界。
- [ ] `agent_memory/progress.md` 已记录执行进度。
- [ ] `agent_memory/bugs.md` 已记录真实问题或风险。
- [ ] 聚焦测试全部通过。
- [ ] `py_compile` 通过。
- [ ] ClaudeCode alignment matrix 达到预期。
- [ ] 真实可见终端交互验收通过，或明确声明未完成且不能宣称开发完成。

## 6. 自检结果

规格覆盖：

- 系统剪贴板对齐：Task 2、Task 3。
- 权限审批语义对齐：Task 4。
- CA07/CA13/CA14 矩阵对齐：Task 5、Task 6、Task 7。
- 排除外部 MCP 包和 macOS/Windows 差异：第 0 节、第 4 节。
- 防止长任务跑偏：第 1 节、第 3 节、第 5 节。

红旗词扫描：

- 本计划避免使用空泛占位表达，所有任务都有目标文件、验证命令和期望结果。

类型一致性：

- `clipboard_backend` 统一挂在 `ComputerUseMcpV2Context`。
- 剪贴板后端统一暴露 `backend_name/read_text/write_text`。
- 权限字段沿用 ClaudeCode-compatible 的 `apps/applications/grantFlags/sentinelWarnings`。
- 矩阵仍沿用 `CA07/CA13/CA14` 维度，不把真实缺口误标为系统差异。

