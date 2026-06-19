# Computer Use Notepad Drag Save Pressure Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用真实可见终端验收 OpenHarness agent 是否能打开本地真实记事本，输入 `hello everyone`，用鼠标拖动记事本窗口沿屏幕移动一圈，并保存为桌面 `1.txt`。

**Architecture:** 使用现有 `learning_agent/acceptance_controller/controller.ps1` 启动 `learning_agent/start_oauth_agent.bat`，由 controller 输入固定压力测试 prompt，并保存启动、输入、最终三张截图。新增一个专用场景 JSON 和一个轻量验证器，验证真实 Notepad 进程、桌面文件内容、窗口移动轨迹和反作弊条件。

**Tech Stack:** PowerShell acceptance controller、Windows Notepad、Python unittest/verification script、CodeGraph、现有 `learning_agent.computer_use_mcp_v2` Windows runtime。

---

## 1. 测试定义

本测试中的“旋转一圈”不表示把记事本窗口按角度旋转，因为 Windows 记事本窗口不能像图片一样原地旋转。这里定义为：agent 用真实鼠标拖住记事本标题栏，让窗口沿屏幕上方、右侧、下方、左侧移动一圈，最后回到接近起点的位置。

固定输入分两段，第一段必须先打开 Computer Use full 模式，第二段才输入压力测试任务：

```text
/computer use --full
```

```text
请打开本地真实记事本，并在记事本里输入 hello everyone；然后使用真实鼠标拖住记事本窗口标题栏，让记事本窗口沿屏幕上方、右侧、下方、左侧移动一圈，最后回到接近起点的位置；最后把文件保存为本地电脑桌面上的 1.txt。不要直接用 PowerShell、Python 或命令行写入 1.txt，必须通过真实记事本窗口完成。完成后最后一行输出：NOTEPAD_DRAG_SAVE_PRESSURE_OK hello everyone saved_to_desktop=true real_notepad_used=true mouse_drag_loop=true
```

## 2. 成功标准

- 必须由 `acceptance_controller` 启动真实可见终端窗口。
- 必须先输入 `/computer use --full`，并确认 Computer Use full mode 已进入。
- 必须向真实终端里的 agent 输入固定测试 prompt。
- 必须观察到 agent 最终回答。
- `Desktop\1.txt` 必须存在。
- `Desktop\1.txt` 内容必须包含且只需要包含核心文本 `hello everyone`。
- 必须能证明真实 Notepad 被使用过，而不是直接写文件。
- 必须能证明记事本窗口位置发生至少 4 个方向上的移动采样。
- controller 结果必须包含启动截图、prompt 截图、最终截图。
- agent 最终回答必须包含 `NOTEPAD_DRAG_SAVE_PRESSURE_OK`。

## 3. 禁止行为

- 不允许打开登录页、支付页、密码管理器、注册表、系统设置、安装器、管理员弹窗或 UAC。
- 不允许读取或修改用户私人文档。
- 不允许直接用 PowerShell、Python、cmd、重定向、`Set-Content`、`Out-File` 等方式生成桌面 `1.txt`。
- 不允许覆盖已有 `Desktop\1.txt`，除非测试前已经备份或用户明确确认。
- 不允许在桌面以外的位置保存最终文件后伪称成功。

## 4. 风险控制

- 测试前检查桌面是否已有 `1.txt`。
- 如果已有 `1.txt`，先停止并报告，默认不覆盖。
- 测试过程中只允许使用 Notepad、桌面保存对话框、真实鼠标拖动和必要的 agent 终端。
- 如果出现 UAC、管理员权限请求、系统设置窗口、浏览器登录页，立即停止并判失败。
- 测试失败后保留截图、events.jsonl、result.json 和 debug log，便于复盘。

## 5. 证据文件

计划使用以下证据目录：

```text
H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\runs\
```

每轮测试至少保存：

- `01_startup.png`
- `02_prompt_sent.png`
- `03_final.png`
- `events.jsonl`
- `latest_run_readable.md`
- `result.json`
- `notepad_drag_save_pressure_report.json`

## 6. 实施任务

### Task 1: 预检桌面文件状态

**Files:**
- Read: `C:\Users\<当前用户>\Desktop\1.txt`
- No code change.

- [ ] **Step 1: 检查桌面是否已有 1.txt**

Run:

```powershell
$desktop = [Environment]::GetFolderPath("Desktop")
$target = Join-Path $desktop "1.txt"
if (Test-Path -LiteralPath $target) {
  Write-Host "DESKTOP_1_TXT_EXISTS=$target"
  exit 2
}
Write-Host "DESKTOP_1_TXT_CLEAR=$target"
exit 0
```

Expected:

```text
DESKTOP_1_TXT_CLEAR=...
```

如果输出 `DESKTOP_1_TXT_EXISTS=...`，停止测试，不执行真实桌面动作。

### Task 2: 新增专用 acceptance scenario

**Files:**
- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal.json`

- [ ] **Step 1: 创建场景 JSON**

场景必须包含：

```json
{
  "id": "agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal",
  "name": "agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal",
  "output_prefix": "agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal",
  "window_title_prefix": "LearningAgent-NotepadDragSavePressure",
  "entrypoint": "learning_agent/start_oauth_agent.bat",
  "visible_terminal_gate": true,
  "screenshot_artifacts_required": true,
  "max_seconds": 900,
  "final_log_wait_seconds": 90,
  "post_success_wait_seconds": 8,
  "environment": {
    "LEARNING_AGENT_DANGEROUSLY_SKIP_PERMISSIONS": "0"
  },
  "success_marker": "NOTEPAD_DRAG_SAVE_PRESSURE_OK",
  "multi_prompt_lines": true,
  "prompt_lines": [
    "/computer use --full",
    "请打开本地真实记事本，并在记事本里输入 hello everyone；然后使用真实鼠标拖住记事本窗口标题栏，让记事本窗口沿屏幕上方、右侧、下方、左侧移动一圈，最后回到接近起点的位置；最后把文件保存为本地电脑桌面上的 1.txt。不要直接用 PowerShell、Python 或命令行写入 1.txt，必须通过真实记事本窗口完成。完成后最后一行输出：NOTEPAD_DRAG_SAVE_PRESSURE_OK hello everyone saved_to_desktop=true real_notepad_used=true mouse_drag_loop=true"
  ],
  "required_event_states": [
    "agent_ready_for_user_prompt",
    "computer_status_printed",
    "user_prompt_received",
    "final_answer_printed"
  ],
  "event_payload_contains": [
    "Computer Use Mode",
    "full_mode=true"
  ],
  "event_answer_contains": [
    "NOTEPAD_DRAG_SAVE_PRESSURE_OK",
    "hello everyone",
    "saved_to_desktop=true",
    "real_notepad_used=true",
    "mouse_drag_loop=true"
  ],
  "debug_log_contains": [
    "NOTEPAD_DRAG_SAVE_PRESSURE_OK",
    "hello everyone",
    "saved_to_desktop=true",
    "real_notepad_used=true",
    "mouse_drag_loop=true"
  ],
  "assertions": {
    "output_contains": [
      "NOTEPAD_DRAG_SAVE_PRESSURE_OK",
      "hello everyone",
      "saved_to_desktop=true",
      "real_notepad_used=true",
      "mouse_drag_loop=true"
    ]
  },
  "max_permission_sent_count": 3
}
```

### Task 3: 新增独立验证器

**Files:**
- Create: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\computer_use_mcp_v2\windows_runtime\notepad_drag_save_pressure_verifier.py`
- Test: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\tests\test_notepad_drag_save_pressure_verifier.py`

- [ ] **Step 1: 验证器检查项**

验证器必须检查：

- 桌面 `1.txt` 是否存在。
- 文件内容是否包含 `hello everyone`。
- 最新 acceptance run 是否有三张截图。
- `latest_run_readable.md` 是否没有出现明显直接写文件命令，例如 `Set-Content`、`Out-File`、`python -c` 写桌面文件。
- 如果能从 runtime 记录读取窗口矩形采样，必须确认至少 4 个不同窗口坐标。

- [ ] **Step 2: 验证器通过标记**

验证器成功时输出：

```text
NOTEPAD_DRAG_SAVE_PRESSURE_VERIFY_OK file_exists=true content_verified=true screenshots_verified=true direct_file_write_not_detected=true
```

验证器失败时输出具体失败原因，并返回非零退出码。

### Task 4: 单次真实可见终端验收

**Files:**
- Use: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\controller.ps1`
- Use: `H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal.json`

- [ ] **Step 1: 运行 controller**

Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\controller.ps1" -ScenarioPath "H:\codexworkplace\sofeware\OpenHarness-main\learning_agent\acceptance_controller\scenarios\agent_capability_computer_use_notepad_drag_save_pressure_visible_terminal.json"
```

Expected:

```text
ACCEPTANCE_CONTROLLER_COMPLETED=True
RESULT_JSON=...
```

- [ ] **Step 2: 运行验证器**

Run:

```powershell
python -m learning_agent.computer_use_mcp_v2.windows_runtime.notepad_drag_save_pressure_verifier --repo-root "H:\codexworkplace\sofeware\OpenHarness-main"
```

Expected:

```text
NOTEPAD_DRAG_SAVE_PRESSURE_VERIFY_OK file_exists=true content_verified=true screenshots_verified=true direct_file_write_not_detected=true
```

### Task 5: 压力轮次

**Files:**
- Use: same scenario and verifier as Task 4.

- [ ] **Step 1: 执行 3 轮连续测试**

每一轮都必须先清理或确认 `Desktop\1.txt` 不存在。每轮都生成独立 result 目录。

- [ ] **Step 2: 执行焦点扰动测试**

在不打开高风险应用的前提下，让桌面已有普通窗口存在，观察 agent 是否仍能聚焦 Notepad 并完成保存。

- [ ] **Step 3: 执行失败门禁测试**

人为保留已有 `Desktop\1.txt`，确认测试会停止而不是覆盖。

## 7. 停止条件

以下任一情况出现，立即停止并判失败：

- controller 没有启动真实可见终端。
- `/computer use --full` 没有进入 full mode。
- prompt 没有被 agent 接收。
- agent 使用命令行直接写入 `1.txt`。
- `Desktop\1.txt` 已存在但测试仍继续覆盖。
- 最终截图、prompt 截图或启动截图缺失。
- 最终回答缺少 `NOTEPAD_DRAG_SAVE_PRESSURE_OK`。
- 文件内容不是 `hello everyone`。
- 出现 UAC、管理员权限、系统设置、登录页或用户私人文档。

## 8. 最终判定

只有同时满足以下条件，才能说该压力测试通过：

- 单次真实可见终端验收通过。
- 验证器通过。
- 3 轮连续测试通过。
- 焦点扰动测试通过。
- 已有 `1.txt` 的失败门禁通过。
- 所有证据文件路径已记录。

如果只完成单次验收，结论只能写成“单次压力测试通过”，不能写成“压力测试体系通过”。
