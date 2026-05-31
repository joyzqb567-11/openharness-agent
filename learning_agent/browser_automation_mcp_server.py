"""真实浏览器自动化 MCP server：通过 Python Playwright 控制独立 Chromium。"""  # 新增代码+BrowserAutomation说明: 说明本文件的职责；若省略: 初学者打开文件时不知道这是浏览器自动化 MCP server

from __future__ import annotations  # 新增代码+BrowserAutomation类型: 让类型注解延迟解析；若省略: 某些前向类型写法在运行时可能更脆弱

import json  # 新增代码+BrowserAutomation协议: 读写 JSON-RPC 消息；若省略: MCP server 无法解析请求或返回响应
import math  # 新增代码+BrowserAutomation参数: 检查数字是否为有限值；若省略: 超大值或非有限数字可能绕过参数保护
import re  # 新增代码+BrowserAutomation文本: 归一化页面文本空白；若省略: 后续快照文本可能出现杂乱换行和空格
import subprocess  # 新增代码+RealChrome连接: 启动带本机 CDP 参数的 Chrome 进程；若省略: Task 4 无法真正打开用户确认后的 Chrome
import sys  # 新增代码+BrowserAutomation进程: 访问 stdin、stdout 和启动参数；若省略: server 不能作为 stdio MCP 进程工作
import threading  # 新增代码+BrowserAutomation下载并发: 为下载保存提供互斥锁；若省略: 同名下载事件并发时可能选到同一个文件名
import time  # 新增代码+BrowserAutomation等待: 为后续 browser_wait 预留时间能力；若省略: 后续实现等待工具时缺少标准时间模块
from pathlib import Path  # 新增代码+BrowserAutomation路径: 处理工作区和产物目录路径；若省略: 截图、下载等产物无法稳定定位
from typing import Any  # 新增代码+BrowserAutomation类型: 标注 JSON 字典里的任意值；若省略: 代码可读性和编辑器提示都会变差

try:  # 修改代码+RealChrome导入: 先按包路径导入真实 Chrome helper；若省略: 作为模块导入时可能缺少标准包路径支持
    from learning_agent.browser_real_chrome import (  # 修改代码+RealChrome导入: 引入真实 Chrome helper 接口边界；若省略: Task 4 连接实现无法复用已验证 helper
        BrowserAuditLogger,  # 修改代码+RealChrome导入: 预留真实 profile 操作审计日志工具；若省略: 后续连接真实 Chrome 时缺少审计边界
        BrowserSafetyPolicy,  # 修改代码+RealChrome导入: 预留真实 profile 敏感脚本拦截策略；若省略: 后续真实 Chrome 模式缺少隐私保护入口
        ChromeProfileManager,  # 修改代码+RealChrome导入: 预留 Chrome 路径、profile 路径和进程状态管理器；若省略: 后续连接实现无法定位用户 Chrome
        RealChromeProfileError,  # 修改代码+RealChrome导入: 预留真实 Chrome 专用错误类型；若省略: 后续无法区分真实 profile 风险错误
        build_chrome_debug_command,  # 修改代码+RealChrome导入: 预留本机调试 Chrome 启动命令构造函数；若省略: 后续启动命令容易散落重复
        choose_loopback_port,  # 修改代码+RealChrome导入: 预留只绑定本机回环地址的端口选择能力；若省略: 后续调试端口可能缺少安全选择边界
        wait_for_cdp_endpoint,  # 修改代码+RealChrome导入: 预留 CDP 端点就绪等待 helper；若省略: 后续连接可能在 Chrome 未就绪时抢跑失败
    )  # 修改代码+RealChrome导入: 结束包路径 helper 导入列表；若省略: Python 多行导入语法不完整
except ModuleNotFoundError as import_error:  # 修改代码+RealChrome导入: 捕获包路径缺失并保留错误对象；若省略: 无法区分脚本模式导入失败和 helper 内部依赖缺失
    if import_error.name not in {"learning_agent", "learning_agent.browser_real_chrome"}:  # 修改代码+RealChrome导入: 只在包路径本身不可用时 fallback；若省略: helper 内部缺依赖会被隐藏成脚本模式导入
        raise  # 修改代码+RealChrome导入: 重新抛出 helper 内部依赖错误；若省略: 真实错误会被吞掉导致排查方向错误
    from browser_real_chrome import (  # 修改代码+RealChrome导入: 脚本模式下从同目录导入 helper；若省略: 端到端 MCP 测试无法启动 server
        BrowserAuditLogger,  # 修改代码+RealChrome导入: 脚本模式预留真实 profile 操作审计日志工具；若省略: fallback 分支缺少审计边界
        BrowserSafetyPolicy,  # 修改代码+RealChrome导入: 脚本模式预留敏感脚本拦截策略；若省略: fallback 分支缺少隐私保护入口
        ChromeProfileManager,  # 修改代码+RealChrome导入: 脚本模式预留 Chrome profile 管理器；若省略: fallback 分支无法定位用户 Chrome
        RealChromeProfileError,  # 修改代码+RealChrome导入: 脚本模式预留真实 Chrome 专用错误类型；若省略: fallback 分支无法区分真实 profile 风险错误
        build_chrome_debug_command,  # 修改代码+RealChrome导入: 脚本模式预留调试命令构造函数；若省略: fallback 分支后续启动命令无法复用 helper
        choose_loopback_port,  # 修改代码+RealChrome导入: 脚本模式预留本机端口选择能力；若省略: fallback 分支后续缺少安全端口选择
        wait_for_cdp_endpoint,  # 修改代码+RealChrome导入: 脚本模式预留 CDP 等待 helper；若省略: fallback 分支后续连接可能抢跑失败
    )  # 修改代码+RealChrome导入: 结束脚本模式 helper 导入列表；若省略: Python 多行导入语法不完整

try:  # 修改代码+BrowserSplit: 优先从 browser 包导入产物路径安全 helper；若没有这行代码，浏览器产物路径规则仍只能留在本 server 内部。
    from learning_agent.browser.artifacts import safe_browser_artifact_path  # 修改代码+BrowserSplit: 包运行模式下导入安全产物路径函数；若没有这行代码，截图和下载无法复用新 browser 层。
except ModuleNotFoundError as import_error:  # 修改代码+BrowserSplit: 捕获直接作为 MCP server 脚本运行时的包路径缺失；若没有这行代码，stdio server 启动可能找不到 learning_agent.browser。
    if import_error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.artifacts"}:  # 修改代码+BrowserSplit: 只允许目标包路径缺失时 fallback；若没有这行代码，artifacts 内部真实 bug 会被误吞。
        raise  # 修改代码+BrowserSplit: 非路径问题继续抛出；若没有这行代码，真实导入错误会被伪装成脚本模式问题。
    from browser.artifacts import safe_browser_artifact_path  # 修改代码+BrowserSplit: 脚本模式下从同目录 browser 包导入 helper；若没有这行代码，MCP server 直接启动时会缺少路径清洗函数。

try:  # 新增代码+BrowserAutomation依赖: 尝试导入真实 Playwright；若省略: 无法区分依赖缺失和运行时错误
    from playwright.sync_api import Error as PlaywrightError  # 新增代码+BrowserAutomation依赖: 导入 Playwright 通用错误类型；若省略: 后续实现无法精确捕获浏览器错误
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError  # 新增代码+BrowserAutomation依赖: 导入 Playwright 超时错误类型；若省略: 后续实现无法给超时返回友好提示
    from playwright.sync_api import sync_playwright  # 新增代码+BrowserAutomation依赖: 导入同步 Playwright 启动入口；若省略: 后续无法启动独立 Chromium
except Exception as import_error:  # 新增代码+BrowserAutomation依赖: 捕获 Playwright 未安装等导入失败；若省略: tools/list 会因为缺依赖直接崩溃
    PlaywrightError = RuntimeError  # 新增代码+BrowserAutomation依赖: 用 RuntimeError 兜底错误类型；若省略: 后续引用 PlaywrightError 会 NameError
    PlaywrightTimeoutError = RuntimeError  # 新增代码+BrowserAutomation依赖: 用 RuntimeError 兜底超时类型；若省略: 后续引用 PlaywrightTimeoutError 会 NameError
    sync_playwright = None  # 新增代码+BrowserAutomation依赖: 标记 Playwright 当前不可用；若省略: 无法在调用时给出安装指引
    PLAYWRIGHT_IMPORT_ERROR = import_error  # 新增代码+BrowserAutomation依赖: 保存原始导入错误；若省略: 用户排查依赖缺失时信息不足
else:  # 新增代码+BrowserAutomation依赖: 处理 Playwright 导入成功分支；若省略: 成功时缺少统一状态标记
    PLAYWRIGHT_IMPORT_ERROR = None  # 新增代码+BrowserAutomation依赖: 标记 Playwright 已可导入；若省略: 后续可能误判依赖缺失

if hasattr(sys.stdin, "reconfigure"):  # 新增代码+BrowserAutomation编码: 检查 stdin 是否支持重设编码；若省略: 旧 Python 环境可能没有该方法而报错
    sys.stdin.reconfigure(encoding="utf-8")  # 新增代码+BrowserAutomation编码: 强制按 UTF-8 读取 MCP 请求；若省略: Windows 管道里的中文参数可能乱码
if hasattr(sys.stdout, "reconfigure"):  # 新增代码+BrowserAutomation编码: 检查 stdout 是否支持重设编码；若省略: 旧 Python 环境可能没有该方法而报错
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")  # 新增代码+BrowserAutomation编码: 强制按 UTF-8 和单行换行输出；若省略: MCP client 可能读不到稳定中文 JSON

WORKSPACE = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else Path.cwd().resolve()  # 新增代码+BrowserAutomation工作区: 使用启动参数指定工作区，缺省用当前目录；若省略: server 不知道产物应放在哪里
ARTIFACTS_DIR = WORKSPACE / "browser_artifacts"  # 新增代码+BrowserAutomation产物: 统一保存截图、下载等浏览器产物；若省略: 后续文件输出会散落难找
DEFAULT_TIMEOUT_MS = 5000  # 新增代码+BrowserAutomation超时: 设置默认操作超时为 5 秒；若省略: 后续操作可能无限等待或没有统一默认值
MAX_TIMEOUT_MS = 30000  # 新增代码+BrowserAutomation超时: 限制最长操作超时为 30 秒；若省略: 模型可能传入过长等待拖死任务
DEFAULT_MAX_CHARS = 4000  # 新增代码+BrowserAutomation输出: 设置默认文本返回长度；若省略: 页面快照可能一次返回太多内容
MAX_RESULT_CHARS = 20000  # 新增代码+BrowserAutomation输出: 设置最大文本返回长度；若省略: 超长页面可能撑爆上下文


def ensure_playwright_available() -> None:  # 新增代码+BrowserAutomation依赖检查: 定义 Playwright 可用性检查函数；若省略: 后续工具无法给出清楚安装指引
    if sync_playwright is None:  # 新增代码+BrowserAutomation依赖检查: 判断导入入口是否缺失；若省略: 依赖缺失会在更深层变成难懂错误
        raise RuntimeError(f"Playwright 不可用，请用 bundled Python 运行：python -m pip install playwright，然后运行：python -m playwright install chromium。原始错误：{PLAYWRIGHT_IMPORT_ERROR}")  # 新增代码+BrowserAutomation依赖检查: 抛出中文安装提示；若省略: 用户不知道该装 pip 包和 Chromium


def safe_int(value: Any, default: int, minimum: int, maximum: int) -> int:  # 新增代码+BrowserAutomation参数: 安全转换整数参数；若省略: 工具参数容易因为坏输入崩溃
    try:  # 新增代码+BrowserAutomation参数: 捕获类型、数值和溢出异常；若省略: None、对象或无穷大可能直接报错
        if isinstance(value, bool):  # 修改代码+BrowserAutomation参数: bool 是 int 的子类但不能当 timeout/max_entries；若省略: True 会被误当成 1
            number = default  # 修改代码+BrowserAutomation参数: bool 参数回退默认值；若省略: 布尔值会悄悄改变等待时间或返回数量
        else:  # 修改代码+BrowserAutomation参数: 只有非 bool 值才进入普通整数转换；若省略: 正常数字字符串无法继续按原逻辑处理
            number = int(value)  # 修改代码+BrowserAutomation参数: 尝试把输入转成整数；若省略: JSON 里的数字字符串无法被接受
        if not math.isfinite(float(number)):  # 新增代码+BrowserAutomation参数: 防御非有限数字；若省略: 特殊数字可能绕过上下限逻辑
            number = default  # 新增代码+BrowserAutomation参数: 非有限数字回退默认值；若省略: 后续 clamp 可能处理异常值
    except (TypeError, ValueError, OverflowError):  # 新增代码+BrowserAutomation参数: 处理无法转换的输入；若省略: 坏参数会让整个工具调用失败
        number = default  # 新增代码+BrowserAutomation参数: 转换失败时使用默认值；若省略: 用户一次传错参数就会中断流程
    return max(minimum, min(maximum, number))  # 新增代码+BrowserAutomation参数: 把整数夹在安全范围内；若省略: 过大或过小参数会影响稳定性


def normalize_spaces(value: str) -> str:  # 新增代码+BrowserAutomation文本: 定义空白归一化 helper；若省略: 多处文本清理会重复写正则
    return re.sub(r"\s+", " ", value).strip()  # 新增代码+BrowserAutomation文本: 把连续空白压成单空格并去掉两端空白；若省略: 返回内容可读性会变差


def clip_text(value: Any, max_chars: int) -> tuple[str, bool]:  # 新增代码+BrowserAutomation输出: 定义安全截断 helper；若省略: 工具可能返回超长或非字符串内容
    try:  # 修改代码+BrowserAutomation输出: 先把最大长度规范成整数；若省略: 非数字长度会导致截断判断报错
        safe_limit = max(1, int(max_chars))  # 修改代码+BrowserAutomation输出: 最小允许长度为 1，避免 -1 变成 text[:-1]；若省略: 负数会产生隐蔽截断
    except (TypeError, ValueError, OverflowError):  # 修改代码+BrowserAutomation输出: 捕获无法转换的长度；若省略: 坏 max_chars 会让工具调用失败
        safe_limit = DEFAULT_MAX_CHARS  # 修改代码+BrowserAutomation输出: 坏长度回退默认输出上限；若省略: 调用方传错长度时没有稳定兜底
    if isinstance(value, str):  # 新增代码+BrowserAutomation输出: 判断值是否已经是字符串；若省略: 字符串会被重复 JSON 编码变得难读
        text = value  # 新增代码+BrowserAutomation输出: 字符串保持原样；若省略: 文本结果可能多出引号和转义符
    else:  # 新增代码+BrowserAutomation输出: 处理非字符串值；若省略: 字典列表等结果无法统一返回
        text = json.dumps(value, ensure_ascii=False, default=str)  # 新增代码+BrowserAutomation输出: 非字符串转成可读 JSON；若省略: 复杂对象可能无法序列化
    if len(text) > safe_limit:  # 修改代码+BrowserAutomation输出: 使用规范化后的安全长度判断是否超限；若省略: 负数或坏长度会造成隐蔽错误
        return text[:safe_limit], True  # 修改代码+BrowserAutomation输出: 按安全长度截断并标记已截断；若省略: 调用方不知道内容不完整
    return text, False  # 新增代码+BrowserAutomation输出: 返回完整文本并标记未截断；若省略: 调用方无法区分完整和截断


def make_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:  # 新增代码+BrowserAutomation协议: 构造 JSON-RPC 成功响应；若省略: 每个分支都会重复写响应结构
    return {"jsonrpc": "2.0", "id": request_id, "result": result}  # 新增代码+BrowserAutomation协议: 返回带 id 的标准成功对象；若省略: client 无法匹配请求和结果


def make_error(request_id: Any, code: int, message: str) -> dict[str, Any]:  # 新增代码+BrowserAutomation协议: 构造 JSON-RPC 错误响应；若省略: 失败时没有统一格式
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}  # 新增代码+BrowserAutomation协议: 返回标准错误对象；若省略: client 难以读取失败原因


def tool_result(text: str) -> dict[str, Any]:  # 新增代码+BrowserAutomation协议: 把普通文本包装成 MCP content；若省略: tools/call 返回格式不符合 MCP 习惯
    return {"content": [{"type": "text", "text": text}]}  # 新增代码+BrowserAutomation协议: 返回标准文本 content；若省略: learning_agent 难以提取工具结果


TOOLS: list[dict[str, Any]] = [  # 新增代码+BrowserAutomation工具清单: 定义成熟版浏览器自动化工具列表；若省略: tools/list 无法暴露能力
    {"name": "browser_open", "description": "打开指定 URL，并在独立 Chromium 中创建或复用页面；不用于真实 Chrome、真实浏览器、桌面可见浏览器或登录态请求，这些请求必须先走 browser_profile_status 和 browser_connect_real_chrome workflow。", "inputSchema": {"type": "object", "properties": {"url": {"type": "string", "description": "要打开的 http、https 或本地测试页面 URL。"}, "new_tab": {"type": "boolean", "description": "是否强制在新标签页打开。"}, "timeout_ms": {"type": "integer", "description": "打开页面的超时时间，默认 5000，最大 30000。"}}, "required": ["url"]}},  # 修改代码+PromptSurfaceV2: 明确 browser_open 是独立 Chromium 且不替代真实 Chrome；若没有这行代码，模型可能把用户要求的真实浏览器误导到普通 browser_open
    {"name": "browser_snapshot", "description": "获取当前页面的可访问性快照和文本摘要。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要读取快照的页面 id，缺省使用当前页面。"}, "max_text_chars": {"type": "integer", "description": "最多返回多少文本字符，默认 4000，最大 20000。"}, "max_elements": {"type": "integer", "description": "最多返回多少个可交互元素。"}}}},  # 修改代码+BrowserAutomation快照: 按规格使用 page_id/max_text_chars/max_elements；若省略: 后续实现和调用方参数会对不上
    {"name": "browser_click", "description": "点击当前页面中的元素引用、选择器或文本目标。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要操作的页面 id，缺省使用当前页面。"}, "element_id": {"type": "string", "description": "页面快照中返回的元素 id。"}, "selector": {"type": "string", "description": "要点击的 CSS 选择器。"}, "text": {"type": "string", "description": "要点击的可见文本。"}, "exact": {"type": "boolean", "description": "文本匹配是否必须完全一致。"}, "timeout_ms": {"type": "integer", "description": "点击等待超时时间，默认 5000，最大 30000。"}}}},  # 修改代码+BrowserAutomation点击: 按规格移除 ref 并加入 page_id/element_id/selector/exact；若省略: agent 会用错点击参数
    {"name": "browser_type", "description": "向输入框或当前焦点输入文本。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要操作的页面 id，缺省使用当前页面。"}, "element_id": {"type": "string", "description": "页面快照中返回的元素 id。"}, "selector": {"type": "string", "description": "要输入的 CSS 选择器。"}, "label": {"type": "string", "description": "要匹配的表单标签文本。"}, "text": {"type": "string", "description": "要输入的文本。"}, "clear": {"type": "boolean", "description": "输入前是否清空原内容。"}, "timeout_ms": {"type": "integer", "description": "输入等待超时时间，默认 5000，最大 30000。"}}, "required": ["text"]}},  # 修改代码+BrowserAutomation输入: 按规格移除 ref 并加入 page_id/element_id/selector/label；若省略: 表单输入调用参数会不兼容
    {"name": "browser_press_key", "description": "在当前页面按下键盘按键。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要操作的页面 id，缺省使用当前页面。"}, "key": {"type": "string", "description": "要按下的按键，例如 Enter、Escape、Control+A。"}}, "required": ["key"]}},  # 修改代码+BrowserAutomation按键: 按规格只保留 page_id/key；若省略: schema 会包含非规格 timeout_ms
    {"name": "browser_wait", "description": "等待指定毫秒数、元素、文本、URL 或页面加载状态。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要等待的页面 id，缺省使用当前页面。"}, "milliseconds": {"type": "integer", "description": "要等待的毫秒数。"}, "selector": {"type": "string", "description": "要等待出现的 CSS 选择器。"}, "text": {"type": "string", "description": "要等待出现的文本。"}, "url_contains": {"type": "string", "description": "等待当前 URL 包含这段文本。"}, "load_state": {"type": "string", "description": "等待的页面加载状态，例如 load、domcontentloaded、networkidle。"}, "timeout_ms": {"type": "integer", "description": "等待上限，默认 5000，最大 30000。"}}}},  # 修改代码+BrowserAutomation等待: 按规格使用 milliseconds 并补齐等待条件；若省略: 等待工具参数会和设计不一致
    {"name": "browser_screenshot", "description": "截取当前页面图片并保存到 browser_artifacts。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要截图的页面 id，缺省使用当前页面。"}, "filename": {"type": "string", "description": "截图文件名，建议使用 .png。"}, "full_page": {"type": "boolean", "description": "是否截取整页。"}}}},  # 修改代码+BrowserAutomation截图: 按规格只保留 page_id/filename/full_page；若省略: 截图 schema 会包含非规格字段
    {"name": "browser_tabs", "description": "列出、切换、新建或关闭浏览器标签页。", "inputSchema": {"type": "object", "properties": {"action": {"type": "string", "description": "操作类型：list、switch、new、close。"}, "page_id": {"type": "string", "description": "要切换或关闭的页面 id。"}, "url": {"type": "string", "description": "新建标签页时要打开的 URL。"}}}},  # 修改代码+BrowserAutomation标签页: 按规格加入 url 并把 action 描述改为 list/switch/new/close；若省略: agent 会使用错误 select 动作
    {"name": "browser_console", "description": "读取页面 console 日志。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要读取日志的页面 id，缺省使用当前页面。"}, "max_entries": {"type": "integer", "description": "最多返回多少条日志。"}}}},  # 修改代码+BrowserAutomation控制台: 按规格保留 page_id/max_entries 并移除 clear；若省略: 控制台工具 schema 会暴露非规格参数
    {"name": "browser_network", "description": "读取页面网络请求记录。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要读取网络记录的页面 id，缺省使用当前页面。"}, "max_entries": {"type": "integer", "description": "最多返回多少条网络记录。"}}}},  # 修改代码+BrowserAutomation网络: 按规格保留 page_id/max_entries 并移除 clear；若省略: 网络工具 schema 会暴露非规格参数
    {"name": "browser_upload_file", "description": "向文件选择控件上传工作区内文件。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要操作的页面 id，缺省使用当前页面。"}, "selector": {"type": "string", "description": "文件输入框的 CSS 选择器。"}, "element_id": {"type": "string", "description": "页面快照中返回的文件输入元素 id。"}, "path": {"type": "string", "description": "要上传的工作区内文件路径。"}}, "required": ["path"]}},  # 修改代码+BrowserAutomation上传: 按规格移除 ref 并加入 page_id/selector/element_id/path；若省略: 文件上传调用会使用错误字段
    {"name": "browser_downloads", "description": "列出浏览器下载记录。", "inputSchema": {"type": "object", "properties": {"max_results": {"type": "integer", "description": "最多返回多少条下载记录。"}}}},  # 修改代码+BrowserAutomation下载: 按规格使用 max_results 并移除 action；若省略: 下载工具 schema 会和设计不一致
    {"name": "browser_evaluate", "description": "在当前页面执行 JavaScript 并返回结果。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要执行脚本的页面 id，缺省使用当前页面。"}, "script": {"type": "string", "description": "要在页面中执行的 JavaScript 代码。"}, "timeout_ms": {"type": "integer", "description": "执行脚本超时时间，默认 5000，最大 30000。"}, "max_result_chars": {"type": "integer", "description": "最多返回多少结果字符，默认 4000，最大 20000。"}}, "required": ["script"]}},  # 修改代码+BrowserAutomation脚本: 按规格使用 page_id/script/timeout_ms/max_result_chars；若省略: evaluate 参数会和后续实现不兼容
    {"name": "browser_close", "description": "关闭指定页面或全部浏览器状态。", "inputSchema": {"type": "object", "properties": {"page_id": {"type": "string", "description": "要关闭的页面 id，缺省按 all 参数决定。"}, "all": {"type": "boolean", "description": "是否关闭全部页面、上下文和浏览器。"}}}},  # 修改代码+BrowserAutomation关闭: 按规格加入 page_id/all；若省略: agent 无法表达关闭单页或全部资源
    {"name": "browser_connect_real_chrome", "description": "高风险工具：连接用户真实日常 Chrome profile，可能接触登录态、浏览记录和敏感页面；必须由用户显式确认 confirm_real_profile=true，且检测到 Chrome 未运行后，才会启动/连接本机 127.0.0.1 CDP 的真实 Chrome profile。", "inputSchema": {"type": "object", "properties": {"confirm_real_profile": {"type": "boolean", "const": True, "description": "必须显式为 true，表示用户确认接入真实日常 Chrome profile 的高风险边界。"}, "chrome_path": {"type": "string", "description": "可选 Chrome 可执行文件路径。"}, "user_data_dir": {"type": "string", "description": "可选 Chrome User Data 目录。"}, "profile_directory": {"type": "string", "description": "可选 profile 目录名，例如 Default 或 Profile 1。"}, "debug_port": {"type": "integer", "description": "可选本机调试端口。"}}, "required": ["confirm_real_profile"]}},  # 修改代码+RealChrome规格修复: 描述真实说明确认后会启动/连接本机 127.0.0.1 CDP，不再保留临时桩文案；若省略: 用户会被旧 Task 3 描述误导
    {"name": "browser_disconnect_real_chrome", "description": "断开真实 Chrome CDP 连接；默认 close_browser=false，不关闭 Chrome；仅当 close_browser=true 且存在 agent 启动的 chrome_process 时才请求 terminate。", "inputSchema": {"type": "object", "properties": {"close_browser": {"type": "boolean", "description": "默认 false，不关闭 Chrome；只有为 true 且存在 agent 启动的 chrome_process 时才请求 terminate。", "default": False}}}},  # 修改代码+RealChrome断开说明: 更新断开工具 schema 为当前正式行为；若没有这行代码，用户会继续看到 Task3 临时桩和不准确关闭说明
    {"name": "browser_profile_status", "description": "只读状态工具：查看当前浏览器自动化模式和真实 Chrome 连接状态，不读取 cookie、localStorage、页面内容或任何 profile 敏感数据。", "inputSchema": {"type": "object", "properties": {}}},  # 新增代码+RealChrome工具清单: 暴露只读 profile 状态 schema；若省略: 用户无法确认当前仍是独立 Chromium 模式
]  # 修改代码+RealChrome工具清单: 结束包含 17 个工具的定义；若省略: Python 列表语法不完整


class BrowserAutomationServer:  # 新增代码+BrowserAutomation服务: 定义浏览器自动化 server 状态类；若省略: tools/call 无法复用浏览器状态
    def __init__(self, workspace: Path) -> None:  # 新增代码+BrowserAutomation服务: 初始化 server 工作区和运行状态；若省略: 后续工具没有共享状态
        self.workspace = workspace.resolve()  # 新增代码+BrowserAutomation服务: 保存解析后的工作区路径；若省略: 相对路径和产物定位可能混乱
        self.artifacts_dir = self.workspace / "browser_artifacts"  # 新增代码+BrowserAutomation服务: 保存浏览器产物目录；若省略: 截图下载没有统一位置
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+BrowserAutomation服务: 确保产物目录存在；若省略: 后续保存文件会因为目录缺失失败
        self.playwright: Any = None  # 新增代码+BrowserAutomation状态: 保存 Playwright 管理对象；若省略: 无法在关闭时 stop
        self.browser: Any = None  # 新增代码+BrowserAutomation状态: 保存 Chromium 浏览器对象；若省略: 无法复用或关闭浏览器
        self.context: Any = None  # 新增代码+BrowserAutomation状态: 保存浏览器上下文对象；若省略: 无法管理页面、下载和权限
        self.pages: dict[str, Any] = {}  # 新增代码+BrowserAutomation状态: 保存 page_id 到页面对象的映射；若省略: 多标签页无法定位
        self.next_page_index = 1  # 新增代码+BrowserAutomation标签页: 保存下一个单调递增页面编号，避免关闭旧页后 page_id 被复用覆盖仍存在的页面；若省略: 关闭 page-1 后新建页面可能覆盖 page-2 映射
        self.current_page_id: str | None = None  # 新增代码+BrowserAutomation状态: 记录当前页面 id；若省略: 工具不知道该操作哪个页面
        self.element_refs: dict[str, Any] = {}  # 新增代码+BrowserAutomation状态: 保存快照元素引用；若省略: 点击和输入无法通过 ref 找元素
        self.console_logs: list[dict[str, Any]] = []  # 新增代码+BrowserAutomation状态: 缓存 console 日志；若省略: browser_console 没有数据来源
        self.network_logs: list[dict[str, Any]] = []  # 新增代码+BrowserAutomation状态: 缓存网络日志；若省略: browser_network 没有数据来源
        self.downloads: list[dict[str, Any]] = []  # 新增代码+BrowserAutomation状态: 缓存下载记录；若省略: browser_downloads 没有数据来源
        self.download_lock = threading.Lock()  # 新增代码+BrowserAutomation下载并发: 串行化下载命名和保存；若省略: 两个同名下载可能同时选择同一路径并覆盖
        self.reserved_artifact_paths: set[Path] = set()  # 新增代码+BrowserAutomation下载并发: 记录正在保存但尚未落盘的产物路径；若省略: 并发下载会在文件存在前选到同名路径
        self.session_mode = "independent_chromium"  # 新增代码+RealChrome状态: 保存当前浏览器模式；若省略: 状态工具无法区分独立 Chromium 和真实 Chrome
        self.chrome_process: Any = None  # 新增代码+RealChrome状态: 保存本次由 agent 启动的 Chrome 进程；若省略: 连接失败或后续断开时无法清理本次启动对象
        self.real_chrome_endpoint = ""  # 新增代码+RealChrome状态: 保存 CDP endpoint 摘要；若省略: 用户无法确认连接的是哪个本机端口
        self.real_chrome_profile_summary = ""  # 新增代码+RealChrome状态: 保存 profile 路径摘要；若省略: 状态工具无法说明当前真实 Chrome profile 来源
        self.last_safety_refusal = "无"  # 新增代码+RealChrome安全: 保存最近一次安全拒绝原因；若省略: 状态工具无法解释最近为什么拒绝高风险操作
        self.safety_policy = BrowserSafetyPolicy()  # 新增代码+RealChrome安全: 创建敏感脚本拦截策略对象；若省略: 后续真实 Chrome 模式缺少隐私保护入口
        self.audit_logger = BrowserAuditLogger(self.artifacts_dir / "real_chrome_audit.jsonl")  # 新增代码+RealChrome审计: 创建真实 Chrome 审计日志写入器；若省略: 高风险连接没有最小审计记录

    def call(self, name: str, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation分发: 工具方法统一返回文本结果；若省略: 协议层无法正确包装 MCP content 文本
        dispatch = {  # 新增代码+BrowserAutomation分发: 建立工具名到方法的映射；若省略: 需要大量重复 if 分支
            "browser_open": self.browser_open,  # 新增代码+BrowserAutomation分发: 分发打开页面工具；若省略: browser_open 会被当成未知工具
            "browser_snapshot": self.browser_snapshot,  # 新增代码+BrowserAutomation分发: 分发页面快照工具；若省略: browser_snapshot 会被当成未知工具
            "browser_click": self.browser_click,  # 新增代码+BrowserAutomation分发: 分发点击工具；若省略: browser_click 会被当成未知工具
            "browser_type": self.browser_type,  # 新增代码+BrowserAutomation分发: 分发输入工具；若省略: browser_type 会被当成未知工具
            "browser_press_key": self.browser_press_key,  # 新增代码+BrowserAutomation分发: 分发按键工具；若省略: browser_press_key 会被当成未知工具
            "browser_wait": self.browser_wait,  # 新增代码+BrowserAutomation分发: 分发等待工具；若省略: browser_wait 会被当成未知工具
            "browser_screenshot": self.browser_screenshot,  # 新增代码+BrowserAutomation分发: 分发截图工具；若省略: browser_screenshot 会被当成未知工具
            "browser_tabs": self.browser_tabs,  # 新增代码+BrowserAutomation分发: 分发标签页工具；若省略: browser_tabs 会被当成未知工具
            "browser_console": self.browser_console,  # 新增代码+BrowserAutomation分发: 分发控制台日志工具；若省略: browser_console 会被当成未知工具
            "browser_network": self.browser_network,  # 新增代码+BrowserAutomation分发: 分发网络日志工具；若省略: browser_network 会被当成未知工具
            "browser_upload_file": self.browser_upload_file,  # 新增代码+BrowserAutomation分发: 分发上传工具；若省略: browser_upload_file 会被当成未知工具
            "browser_downloads": self.browser_downloads,  # 新增代码+BrowserAutomation分发: 分发下载记录工具；若省略: browser_downloads 会被当成未知工具
            "browser_evaluate": self.browser_evaluate,  # 新增代码+BrowserAutomation分发: 分发页面脚本工具；若省略: browser_evaluate 会被当成未知工具
            "browser_close": self.browser_close,  # 新增代码+BrowserAutomation分发: 分发关闭工具；若省略: browser_close 会被当成未知工具
            "browser_connect_real_chrome": self.browser_connect_real_chrome,  # 新增代码+RealChrome分发: 分发真实 Chrome 连接临时桩；若省略: schema 可见但 tools/call 会报未知工具
            "browser_disconnect_real_chrome": self.browser_disconnect_real_chrome,  # 新增代码+RealChrome分发: 分发真实 Chrome 断开临时桩；若省略: 用户无法调用断开入口
            "browser_profile_status": self.browser_profile_status,  # 新增代码+RealChrome分发: 分发只读 profile 状态临时桩；若省略: 用户无法查询当前模式
        }  # 新增代码+BrowserAutomation分发: 结束分发表；若省略: Python 字典语法不完整
        if name not in dispatch:  # 新增代码+BrowserAutomation分发: 检查工具名是否存在；若省略: 拼错工具名会触发不清楚的 KeyError
            raise RuntimeError(f"未知工具：{name}")  # 新增代码+BrowserAutomation分发: 返回中文未知工具错误；若省略: 用户难以排查工具名问题
        return dispatch[name](arguments)  # 新增代码+BrowserAutomation分发: 调用目标方法并返回结果；若省略: 已注册工具不会真正进入方法

    def browser_connect_real_chrome(self, arguments: dict[str, Any]) -> str:  # 修改代码+RealChrome连接: 提供真实 Chrome 连接确认边界；若省略: tools/call 无法进入真实 profile 连接流程
        if arguments.get("confirm_real_profile") is not True:  # 修改代码+RealChrome确认: 只接受布尔 True 作为高风险确认；若省略: false、字符串或缺省值可能越过真实 profile 边界
            raise RuntimeError("browser_connect_real_chrome 需要 confirm_real_profile=true，表示用户明确确认接入日常 Chrome profile。")  # 修改代码+RealChrome确认: 用清晰错误提示确认参数；若省略: 用户不知道必须显式确认什么
        manager = ChromeProfileManager()  # 新增代码+RealChrome检测: 创建 Chrome profile 管理器；若省略: 无法检查路径和 Chrome 运行状态
        preferred_port = safe_int(arguments.get("debug_port", 9222), 9222, 1, 65535)  # 新增代码+RealChrome已有CDP: 先解析用户想连接的本机调试端口；若省略: Chrome 已运行时不知道该检查哪个 CDP 端口
        if manager.chrome_is_running():  # 新增代码+RealChrome检测: 检测当前是否已有 Chrome 正在运行；若省略: 可能抢占用户正在使用的 profile
            if wait_for_cdp_endpoint(preferred_port, timeout_seconds=1.0):  # 新增代码+RealChrome已有CDP: 已运行的 Chrome 若已经暴露可信本机 CDP 就直接接管；若省略: 用户必须关闭浏览器才能验收真实可见 Chrome
                return self._connect_real_chrome_after_checks(arguments, manager, attach_existing_cdp=True, existing_debug_port=preferred_port)  # 新增代码+RealChrome已有CDP: 用附着模式连接已有 CDP，不再启动新 Chrome；若省略: 仍可能误启动或继续阻断
            raise RuntimeError("检测到 Chrome 正在运行，请先关闭当前 Chrome，再重试真实 Chrome profile 连接。")  # 新增代码+RealChrome检测: 阻断 profile 锁冲突并给中文操作提示；若省略: 可能损坏或占用日常 profile
        return self._connect_real_chrome_after_checks(arguments, manager)  # 新增代码+RealChrome连接: 通过确认和运行中检查后进入连接 helper；若省略: 确认后不会真正建立 CDP 连接

    def _connect_real_chrome_after_checks(self, arguments: dict[str, Any], manager: ChromeProfileManager, *, attach_existing_cdp: bool = False, existing_debug_port: int | None = None) -> str:  # 修改代码+RealChrome已有CDP: 支持启动新 Chrome 或附着已存在 CDP 两种模式；若省略: 已运行且可调试的桌面 Chrome 仍无法被接管
        chrome_path = Path(str(arguments.get("chrome_path") or "")).expanduser() if str(arguments.get("chrome_path") or "").strip() else manager.find_chrome_path()  # 新增代码+RealChrome路径: 优先使用用户传入 Chrome 路径否则自动发现；若省略: 用户无法覆盖或自动定位 chrome.exe
        user_data_dir = Path(str(arguments.get("user_data_dir") or "")).expanduser() if str(arguments.get("user_data_dir") or "").strip() else manager.find_user_data_dir()  # 新增代码+RealChrome路径: 优先使用用户传入 User Data 路径否则自动发现；若省略: 无法定位真实登录态所在 profile 根目录
        if chrome_path is None or not chrome_path.exists():  # 新增代码+RealChrome路径: 检查 Chrome 可执行文件是否存在；若省略: Popen 会抛出难懂的底层文件错误
            raise RuntimeError("找不到 Chrome 可执行文件，请传入 chrome_path 或安装 Google Chrome。")  # 新增代码+RealChrome路径: 用中文说明缺少浏览器路径；若省略: 用户不知道该补哪个参数
        if user_data_dir is None or not user_data_dir.exists():  # 新增代码+RealChrome路径: 检查 User Data 目录是否存在；若省略: Chrome 可能创建错误的新 profile 或启动失败
            raise RuntimeError("找不到 Chrome User Data 目录，请传入 user_data_dir 或确认本机已创建 Chrome profile。")  # 新增代码+RealChrome路径: 用中文说明缺少 profile 根目录；若省略: 用户不知道登录态目录在哪里出问题
        profile_directory = str(arguments.get("profile_directory") or "Default").strip() or "Default"  # 修改代码+RealChrome隐私: 读取 profile 目录名并默认 Default；若没有这行代码，Chrome 可能无法选择用户期望的身份
        profile_directory_lower = profile_directory.lower()  # 新增代码+RealChrome隐私: 准备小写副本用于识别 AppData 等路径词；若没有这行代码，大小写变化可能绕过路径式输入校验
        profile_directory_has_separator = "/" in profile_directory or "\\" in profile_directory  # 新增代码+RealChrome隐私: 检查 profile_directory 是否包含路径分隔符；若没有这行代码，完整路径可能被当成 profile 名传给 Chrome
        profile_directory_has_path_token = ":" in profile_directory or ".." in profile_directory or profile_directory in (".", "..") or "appdata" in profile_directory_lower  # 新增代码+RealChrome隐私: 检查盘符、上级目录、当前目录和 AppData 等路径特征；若没有这行代码，用户名和目录结构可能进入输出或审计
        if profile_directory_has_separator or profile_directory_has_path_token:  # 新增代码+RealChrome隐私: 拒绝任何路径式 profile_directory；若没有这行代码，调用方误传完整路径时会泄漏本机信息
            raise RuntimeError("profile_directory 目录名非法：只能填写普通 Chrome profile 目录名，例如 Default 或 Profile 1，不能填写路径。")  # 新增代码+RealChrome隐私: 返回不回显原始值的中文错误；若没有这行代码，错误消息可能泄漏用户名或完整目录
        preferred_port = safe_int(arguments.get("debug_port", 9222), 9222, 1, 65535)  # 新增代码+RealChrome端口: 解析用户偏好的本机调试端口；若省略: 坏端口会直接传给 Chrome 导致启动失败
        debug_port = safe_int(existing_debug_port, preferred_port, 1, 65535) if attach_existing_cdp else choose_loopback_port(preferred_port=preferred_port)  # 修改代码+RealChrome已有CDP: 附着模式复用已有 CDP 端口，启动模式才选择空闲端口；若省略: 9222 已可用时仍会跳到随机端口
        endpoint = f"http://127.0.0.1:{debug_port}"  # 新增代码+RealChrome端点: 生成只指向本机的 CDP endpoint；若省略: Playwright 不知道连接哪个地址
        command = None if attach_existing_cdp else build_chrome_debug_command(chrome_path, user_data_dir, profile_directory, debug_port)  # 修改代码+RealChrome已有CDP: 附着已有 CDP 时不构造启动命令；若省略: 接管已开浏览器也可能误启动新进程
        process: Any = None  # 新增代码+RealChrome清理: 先声明本次启动进程变量；若省略: 失败清理分支无法判断是否需要终止 Chrome
        real_browser: Any = None  # 修改代码+RealChrome切换: 使用局部真实 Chrome browser，成功前不覆盖旧独立会话；若省略: 连接失败会误伤旧 browser
        real_context: Any = None  # 修改代码+RealChrome切换: 使用局部真实 Chrome context，成功前不覆盖旧独立上下文；若省略: 连接失败会误伤旧 context
        playwright_driver = self.playwright  # 修改代码+RealChrome切换: 先复用或暂存 Playwright 驱动；若省略: 成功前可能提前改写 self.playwright
        started_playwright = False  # 修改代码+RealChrome切换: 记录本次是否新启动 Playwright；若省略: 失败时不知道能否安全 stop 本次驱动
        old_playwright = self.playwright  # 修改代码+RealChrome事务: 保存旧 Playwright 引用用于失败回滚；若省略: 准备失败后可能留下错误 driver 引用
        old_mode = self.session_mode  # 修改代码+RealChrome事务: 保存旧浏览器模式用于失败回滚；若省略: 失败后状态可能误报 real_chrome
        old_browser = self.browser  # 修改代码+RealChrome事务: 保存旧 browser 引用用于失败回滚和成功后释放；若省略: 失败会丢失独立 Chromium 会话
        old_context = self.context  # 修改代码+RealChrome事务: 保存旧 context 引用用于失败回滚和成功后释放；若省略: 失败会丢失独立 Chromium 上下文
        old_pages = dict(self.pages)  # 修改代码+RealChrome事务: 保存旧页面映射快照；若省略: 页面准备失败会污染原页面表
        old_element_refs = dict(self.element_refs)  # 修改代码+RealChrome事务: 保存旧元素引用快照；若省略: 失败后快照元素可能被清空或串到新会话
        old_current_page_id = self.current_page_id  # 修改代码+RealChrome事务: 保存旧当前页；若省略: 失败后默认操作目标可能丢失
        old_next_page_index = self.next_page_index  # 修改代码+RealChrome事务: 保存旧页面编号游标；若省略: 失败后 page_id 可能跳号或冲突
        old_endpoint = self.real_chrome_endpoint  # 修改代码+RealChrome事务: 保存旧真实 Chrome endpoint 摘要；若省略: 失败后状态字段可能被新端口污染
        old_profile_summary = self.real_chrome_profile_summary  # 修改代码+RealChrome事务: 保存旧 profile 摘要；若省略: 失败后用户可能看到未成功连接的 profile
        old_chrome_process = self.chrome_process  # 修改代码+RealChrome事务: 保存旧进程引用；若省略: 失败后可能误以为本次 Chrome 已成为可管理进程
        old_independent_context = old_context if old_mode == "independent_chromium" else None  # 修改代码+RealChrome事务: 仅把旧独立 Chromium context 标记为成功后可关闭；若省略: 可能误关真实 Chrome context
        old_independent_browser = old_browser if old_mode == "independent_chromium" else None  # 修改代码+RealChrome事务: 仅把旧独立 Chromium browser 标记为成功后可关闭；若省略: 可能误关真实 Chrome browser
        prepared_pages: dict[str, Any] = {}  # 修改代码+RealChrome事务: 用局部页面表准备真实 Chrome 页面；若省略: 准备失败会提前污染 self.pages
        prepared_element_refs: dict[str, Any] = {}  # 修改代码+RealChrome事务: 用局部元素引用表准备新会话；若省略: 准备失败会提前清空旧元素引用
        prepared_current_page_id: str | None = None  # 修改代码+RealChrome事务: 用局部当前页等待最终提交；若省略: 准备失败会提前改写当前页
        prepared_next_page_index = 1  # 修改代码+RealChrome事务: 新真实 Chrome 会话从 page-1 重新编号；若省略: 新旧会话编号会混在一起不易排查
        def real_chrome_committed() -> bool:  # 新增代码+RealChrome事件守卫: 判断真实 Chrome 状态是否已经正式提交；若省略: 准备期事件可能直接改旧会话
            return self.session_mode == "real_chrome" and self.context is real_context  # 新增代码+RealChrome事件守卫: 只有模式和 context 都匹配才允许事件写状态；若省略: 回滚后旧状态仍可能被真实页面事件污染
        def register_real_chrome_page(page: Any) -> None:  # 修改代码+RealChrome事务: 为真实 Chrome 新页面准备提交后才生效的回调；若省略: 提交前触发 page 事件可能污染旧会话
            if real_chrome_committed():  # 修改代码+RealChrome事件守卫: 只在真实 Chrome 已提交后登记新页面；若省略: 准备期 page 事件可能污染旧 pages
                self._register_page(page)  # 修改代码+RealChrome事务: 提交后复用统一页面登记逻辑；若省略: 成功连接后的新标签页不会进入工具页面表
        def forget_real_chrome_page(page_id: str) -> None:  # 新增代码+RealChrome事件守卫: 为真实 Chrome close 事件提供提交守卫；若省略: 准备期 close 事件可能误删旧 page_id
            if real_chrome_committed():  # 新增代码+RealChrome事件守卫: 只在真实 Chrome 已提交后才清理页面映射；若省略: 未提交或已回滚时会改旧 self.pages
                self._forget_page(page_id)  # 新增代码+RealChrome事件守卫: 调用统一页面遗忘逻辑；若省略: 提交后的真实标签页关闭不会同步到本地表
        def record_real_chrome_console(page: Any, message: Any) -> None:  # 新增代码+RealChrome事件守卫: 为真实 Chrome console 事件提供提交守卫；若省略: 准备期 console 事件可能污染旧日志
            if real_chrome_committed():  # 新增代码+RealChrome事件守卫: 只在真实 Chrome 已提交后才记录 console；若省略: 未提交或已回滚时会改旧 console_logs
                self._record_console(page, message)  # 新增代码+RealChrome事件守卫: 调用统一 console 记录逻辑；若省略: 提交后的真实页面 console 不会被收集
        def record_real_chrome_request(page: Any, request: Any) -> None:  # 新增代码+RealChrome事件守卫: 为真实 Chrome request 事件提供提交守卫；若省略: 准备期 request 事件可能污染旧网络日志
            if real_chrome_committed():  # 新增代码+RealChrome事件守卫: 只在真实 Chrome 已提交后才记录 request；若省略: 未提交或已回滚时会改旧 network_logs
                self._record_request(page, request)  # 新增代码+RealChrome事件守卫: 调用统一 request 记录逻辑；若省略: 提交后的真实页面请求不会被收集
        def record_real_chrome_response(page: Any, response: Any) -> None:  # 新增代码+RealChrome事件守卫: 为真实 Chrome response 事件提供提交守卫；若省略: 准备期 response 事件可能污染旧网络日志
            if real_chrome_committed():  # 新增代码+RealChrome事件守卫: 只在真实 Chrome 已提交后才记录 response；若省略: 未提交或已回滚时会改旧 network_logs
                self._record_response(page, response)  # 新增代码+RealChrome事件守卫: 调用统一 response 记录逻辑；若省略: 提交后的真实页面响应不会被收集
        def record_real_chrome_download(page: Any, download: Any) -> None:  # 新增代码+RealChrome事件守卫: 为真实 Chrome download 事件提供提交守卫；若省略: 准备期 download 事件可能污染旧下载记录
            if real_chrome_committed():  # 新增代码+RealChrome事件守卫: 只在真实 Chrome 已提交后才记录 download；若省略: 未提交或已回滚时会改旧 downloads
                self._record_download(page, download)  # 新增代码+RealChrome事件守卫: 调用统一 download 记录逻辑；若省略: 提交后的真实页面下载不会被收集
        try:  # 新增代码+RealChrome清理: 包住启动、等待和连接全过程；若省略: 任一步失败后状态可能半连接残留
            if attach_existing_cdp:  # 新增代码+RealChrome已有CDP: 附着模式不启动 Chrome，只再次确认端点还活着；若省略: 可能误开新浏览器或连接已消失端口
                if not wait_for_cdp_endpoint(debug_port, timeout_seconds=1.0):  # 新增代码+RealChrome已有CDP: 防止检查和连接之间端点消失；若省略: Playwright 会抛出更难懂的连接错误
                    raise RuntimeError(f"已有 Chrome CDP endpoint 未就绪：{endpoint}")  # 新增代码+RealChrome已有CDP: 用中文说明是已有端点不可用；若省略: 用户会以为启动 Chrome 失败
            else:  # 新增代码+RealChrome启动: 非附着模式继续走启动新 Chrome 流程；若省略: 关闭 Chrome 后的正常启动连接会失效
                process = subprocess.Popen(command)  # 新增代码+RealChrome启动: 启动带调试端口的 Chrome；若省略: CDP endpoint 不会出现，后续无法连接
                if not wait_for_cdp_endpoint(debug_port):  # 新增代码+RealChrome等待: 等待 Chrome CDP 端点就绪；若省略: Playwright 可能在 Chrome 未准备好时连接失败
                    raise RuntimeError(f"Chrome 已启动但 CDP endpoint 未就绪：{endpoint}")  # 新增代码+RealChrome等待: 超时时给出端口信息；若省略: 用户不知道卡在哪一步
            ensure_playwright_available()  # 新增代码+RealChrome依赖: 确认 Playwright 可用；若省略: 连接时可能出现更底层的导入错误
            if playwright_driver is None:  # 修改代码+RealChrome依赖: 仅在没有现有驱动时创建局部 Playwright；若省略: 每次连接都可能重复启动驱动
                playwright_driver = sync_playwright().start()  # 修改代码+RealChrome依赖: 启动局部 Playwright 驱动但暂不写入 self；若省略: 无法调用 chromium.connect_over_cdp
                started_playwright = True  # 修改代码+RealChrome依赖: 标记本次新启动驱动；若省略: 失败清理无法安全 stop 新驱动
            real_browser = playwright_driver.chromium.connect_over_cdp(endpoint)  # 修改代码+RealChrome连接: 用局部变量连接真实 Chrome CDP；若省略: 失败前会覆盖旧独立 browser
            if not real_browser.contexts:  # 修改代码+RealChrome连接: 检查 CDP 浏览器是否提供上下文；若省略: 访问 contexts[0] 可能变成难懂的 IndexError
                raise RuntimeError("真实 Chrome 已连接，但没有可用的浏览器上下文。")  # 新增代码+RealChrome连接: 对无 context 场景给清晰中文错误；若省略: 用户无法理解连接为何不可用
            real_context = real_browser.contexts[0]  # 修改代码+RealChrome连接: 使用局部真实 Chrome 上下文等待成功切换；若省略: 失败前会覆盖旧独立 context
            real_context.on("page", register_real_chrome_page)  # 修改代码+RealChrome事务: 提交前验证新页面监听可绑定但回调提交后才会改状态；若省略: 监听失败会在旧会话已关闭后才暴露
            for page in list(real_context.pages):  # 修改代码+RealChrome标签页: 遍历真实 Chrome 已有页面；若省略: 连接后已有标签页无法被工具定位
                page_id = f"page-{prepared_next_page_index}"  # 修改代码+RealChrome事务: 用局部编号为真实 Chrome 页面分配 id；若省略: 无法在提交前准备页面映射
                prepared_next_page_index += 1  # 修改代码+RealChrome事务: 局部推进下一个 page_id；若省略: 多个真实页面会得到重复 id
                prepared_pages[page_id] = page  # 修改代码+RealChrome事务: 把真实页面放入局部页面表；若省略: 成功后 browser_tabs 看不到已有页面
                prepared_current_page_id = page_id  # 修改代码+RealChrome事务: 把最后登记的真实页面设为局部当前页；若省略: 成功后默认页面可能为空
                page.on("close", lambda *args, page_id=page_id: forget_real_chrome_page(page_id))  # 修改代码+RealChrome事件守卫: close 回调先经过提交守卫；若省略: 准备期 close 可能误删旧 page-1
                page.on("console", lambda message, page_ref=page: record_real_chrome_console(page_ref, message))  # 修改代码+RealChrome事件守卫: console 回调先经过提交守卫；若省略: 准备期 console 可能污染旧日志
                page.on("request", lambda request, page_ref=page: record_real_chrome_request(page_ref, request))  # 修改代码+RealChrome事件守卫: request 回调先经过提交守卫；若省略: 准备期 request 可能污染旧网络日志
                page.on("response", lambda response, page_ref=page: record_real_chrome_response(page_ref, response))  # 修改代码+RealChrome事件守卫: response 回调先经过提交守卫；若省略: 准备期 response 可能污染旧网络日志
                page.on("download", lambda download, page_ref=page: record_real_chrome_download(page_ref, download))  # 修改代码+RealChrome事件守卫: download 回调先经过提交守卫；若省略: 准备期 download 可能污染旧下载记录
            self.audit_logger.record("connect_real_chrome", {"profile_directory": profile_directory, "debug_port": debug_port, "page_count": len(prepared_pages), "chrome_path_detected": chrome_path is not None, "user_data_dir_detected": user_data_dir is not None})  # 修改代码+RealChrome隐私: 审计只写 profile 名称、端口、页面数和路径是否存在的布尔摘要；若没有这行代码，Windows 用户名和 User Data 完整路径会进入审计日志
            self.playwright = playwright_driver  # 修改代码+RealChrome事务: 所有准备成功后才提交 Playwright 驱动；若省略: 成功会话缺少驱动引用
            self.browser = real_browser  # 修改代码+RealChrome事务: 所有准备成功后才指向真实 Chrome；若省略: 页面工具无法使用新 CDP 连接
            self.context = real_context  # 修改代码+RealChrome事务: 所有准备成功后才指向真实 Chrome context；若省略: 页面工具没有真实 Chrome 上下文
            self.chrome_process = process  # 修改代码+RealChrome已有CDP: 启动模式保存新进程，附着模式保持 None 避免误关用户原有 Chrome；若省略: 后续断开可能无法区分谁启动了 Chrome
            self.pages = prepared_pages  # 修改代码+RealChrome事务: 原子替换为已准备好的真实 Chrome 页面表；若省略: 页面工具仍会看到旧会话页面
            self.element_refs = prepared_element_refs  # 修改代码+RealChrome事务: 原子替换为空的新元素引用表；若省略: 旧元素 id 会污染真实 Chrome 页面
            self.current_page_id = prepared_current_page_id  # 修改代码+RealChrome事务: 提交已准备好的当前页；若省略: 默认页面操作可能找不到目标
            self.next_page_index = prepared_next_page_index  # 修改代码+RealChrome事务: 提交新会话页面编号游标；若省略: 后续新页面可能复用已有 page_id
            self.session_mode = "real_chrome"  # 新增代码+RealChrome状态: 标记当前处于真实 Chrome 模式；若省略: 状态工具会误报独立 Chromium
            self.real_chrome_endpoint = endpoint  # 新增代码+RealChrome状态: 保存 CDP endpoint 摘要；若省略: 状态和返回文本缺少连接目标
            self.real_chrome_profile_summary = profile_directory  # 修改代码+RealChrome隐私: 只保存 profile 目录名作为非敏感摘要；若没有这行代码，状态和成功返回会泄漏完整 user_data_dir 路径
            if old_independent_context is not None:  # 修改代码+RealChrome事务: 提交成功后才关闭旧独立 context；若省略: 旧独立上下文会不可达残留
                try:  # 修改代码+RealChrome事务: 容忍旧 context 已关闭；若省略: 旧对象异常会阻断已成功的真实 Chrome 连接
                    old_independent_context.close()  # 修改代码+RealChrome事务: 关闭旧独立 Chromium context；若省略: 旧上下文资源无法释放
                except Exception:  # 修改代码+RealChrome事务: 忽略旧 context 关闭异常继续保持新连接；若省略: 清理异常会破坏成功状态
                    pass  # 修改代码+RealChrome事务: 保持 except 分支语法完整；若省略: Python 语法错误
            if old_independent_browser is not None:  # 修改代码+RealChrome事务: 提交成功后才关闭旧独立 browser；若省略: 旧独立 browser 进程会残留
                try:  # 修改代码+RealChrome事务: 容忍旧 browser 已关闭；若省略: 旧对象异常会阻断已成功的真实 Chrome 连接
                    old_independent_browser.close()  # 修改代码+RealChrome事务: 关闭旧独立 Chromium browser；若省略: 旧浏览器进程无法释放
                except Exception:  # 修改代码+RealChrome事务: 忽略旧 browser 关闭异常继续保持新连接；若省略: 清理异常会破坏成功状态
                    pass  # 修改代码+RealChrome事务: 保持 except 分支语法完整；若省略: Python 语法错误
            return "\n".join([  # 新增代码+RealChrome返回: 返回多行成功摘要；若省略: MCP 调用方看不到连接状态
                "browser_connect_real_chrome 成功",  # 新增代码+RealChrome返回: 明确工具成功；若省略: 用户无法快速确认连接完成
                "mode=real_chrome",  # 新增代码+RealChrome返回: 标明当前模式；若省略: 用户可能不知道已切到真实 Chrome
                "real_chrome_connected=true",  # 新增代码+RealChrome返回: 标明连接状态为 true；若省略: 自动化上层无法稳定判断连接成功
                f"profile={self.real_chrome_profile_summary}",  # 新增代码+RealChrome返回: 返回 profile 摘要；若省略: 用户无法核对连接的 profile
                f"endpoint={self.real_chrome_endpoint}",  # 新增代码+RealChrome返回: 返回本机 CDP endpoint；若省略: 排查端口问题更困难
                f"pages={len(self.pages)}",  # 新增代码+RealChrome返回: 返回登记页面数量；若省略: 用户不知道已有标签页是否被识别
            ])  # 新增代码+RealChrome返回: 结束多行摘要拼接；若省略: Python 列表和 join 语法不完整
        except Exception as error:  # 新增代码+RealChrome清理: 捕获连接任一步失败并转成清晰错误；若省略: 半初始化状态可能留在 server 中
            self.playwright = old_playwright  # 修改代码+RealChrome事务: 失败时恢复旧 Playwright 引用；若省略: server 可能指向未提交的临时 driver
            self.session_mode = old_mode  # 修改代码+RealChrome事务: 失败时恢复旧模式；若省略: 状态工具可能误报 real_chrome
            self.browser = old_browser  # 修改代码+RealChrome事务: 失败时恢复旧 browser；若省略: 原独立 Chromium 会话会变成不可达
            self.context = old_context  # 修改代码+RealChrome事务: 失败时恢复旧 context；若省略: 原独立 Chromium 上下文会变成不可达
            self.pages = old_pages  # 修改代码+RealChrome事务: 失败时恢复旧页面映射；若省略: 页面表会被准备阶段污染
            self.element_refs = old_element_refs  # 修改代码+RealChrome事务: 失败时恢复旧元素引用；若省略: 元素快照会被准备阶段污染
            self.current_page_id = old_current_page_id  # 修改代码+RealChrome事务: 失败时恢复旧当前页；若省略: 默认页面操作目标会丢失
            self.next_page_index = old_next_page_index  # 修改代码+RealChrome事务: 失败时恢复旧页面编号游标；若省略: 后续 page_id 可能跳号或冲突
            self.real_chrome_endpoint = old_endpoint  # 修改代码+RealChrome事务: 失败时恢复旧 endpoint 摘要；若省略: 状态会显示未成功连接的新端口
            self.real_chrome_profile_summary = old_profile_summary  # 修改代码+RealChrome事务: 失败时恢复旧 profile 摘要；若省略: 用户可能看到未成功连接的 profile
            self.chrome_process = old_chrome_process  # 修改代码+RealChrome事务: 失败时恢复旧进程引用；若省略: 本次失败进程可能被误认为已接管
            if real_browser is not None:  # 修改代码+RealChrome清理: 只清理本次局部 CDP 连接，不能碰旧 self.browser；若省略: 失败会误伤独立 Chromium 会话
                try:  # 新增代码+RealChrome清理: 容忍关闭连接失败；若省略: 清理错误会盖住原始失败原因
                    disconnect = getattr(real_browser, "disconnect", None)  # 修改代码+RealChrome清理: 优先查找 CDP disconnect；若省略: 可能误用 close 关闭真实 Chrome
                    if callable(disconnect):  # 修改代码+RealChrome清理: 只有存在 disconnect 时才断开；若省略: 无 disconnect 对象会触发调用错误
                        disconnect()  # 修改代码+RealChrome清理: 断开本次 Playwright CDP 连接；若省略: 失败后可能残留 CDP 连接
                except Exception:  # 新增代码+RealChrome清理: 忽略关闭时的附加异常；若省略: 用户看到的可能不是根因
                    pass  # 新增代码+RealChrome清理: 保持 except 分支语法完整；若省略: Python 语法错误
            if started_playwright and playwright_driver is not None:  # 修改代码+RealChrome清理: 只停止本次新建且未切换成功的 Playwright 驱动；若省略: 失败会泄漏新驱动或误停旧驱动
                try:  # 修改代码+RealChrome清理: 容忍 stop 失败；若省略: stop 异常会遮蔽真实连接失败
                    playwright_driver.stop()  # 修改代码+RealChrome清理: 停止本次临时 Playwright 驱动；若省略: 失败路径可能残留驱动进程
                except Exception:  # 修改代码+RealChrome清理: 忽略临时驱动停止异常；若省略: 清理异常会改变错误信息
                    pass  # 修改代码+RealChrome清理: 保持 except 分支语法完整；若省略: Python 语法错误
            if process is not None:  # 新增代码+RealChrome清理: 只清理本次启动过的 Chrome 进程；若省略: 可能误操作不存在的进程对象
                try:  # 新增代码+RealChrome清理: 尽力终止本次启动失败的 Chrome；若省略: 启动失败后 Chrome 可能残留
                    process.terminate()  # 新增代码+RealChrome清理: 请求 Chrome 退出；若省略: 失败连接会留下本次启动的进程
                except Exception:  # 新增代码+RealChrome清理: 容忍进程已经退出；若省略: 清理异常会遮蔽真实连接错误
                    pass  # 新增代码+RealChrome清理: 保持 except 分支语法完整；若省略: Python 语法错误
            raise RuntimeError(f"browser_connect_real_chrome 失败：{error}") from error  # 新增代码+RealChrome清理: 重新抛出清晰错误并保留根因链；若省略: 失败可能被静默吞掉

    def _disconnect_real_chrome_session(self, close_browser: bool) -> dict[str, bool | int]:  # 新增代码+RealChrome断开: 把真实 Chrome 断开流程集中到一个 helper；若没有这行代码，browser_disconnect_real_chrome 和 close_all 容易出现两套不一致行为
        page_count = len(self.pages)  # 新增代码+RealChrome断开: 先记录断开前页面数量用于返回和审计；若没有这行代码，清空 pages 后就无法知道本次断开影响了多少页面映射
        was_real_chrome = self.session_mode == "real_chrome"  # 新增代码+RealChrome断开: 判断当前是否真的处于真实 Chrome 模式；若没有这行代码，无连接幂等调用可能误动独立 Chromium 状态
        disconnected_browser = False  # 新增代码+RealChrome断开: 默认尚未断开 CDP browser；若没有这行代码，返回摘要无法区分是否执行过 disconnect
        terminated_process = False  # 新增代码+RealChrome断开: 默认没有终止 Chrome 进程；若没有这行代码，close_browser=false 的安全结果无法表达
        if was_real_chrome and self.browser is not None:  # 新增代码+RealChrome断开: 只有真实模式且有 browser 对象才尝试断开 CDP；若没有这行代码，None 或独立 Chromium 可能被误处理
            try:  # 新增代码+RealChrome断开: 捕获断开异常以便继续复位本地状态；若没有这行代码，一次 disconnect 失败会让 server 留在半连接状态
                disconnect = getattr(self.browser, "disconnect", None)  # 新增代码+RealChrome断开: 优先查找 Playwright CDP disconnect；若没有这行代码，可能误用 close 关闭真实 Chrome
                if callable(disconnect):  # 新增代码+RealChrome断开: 只有对象支持 disconnect 时才调用；若没有这行代码，没有该方法的 fake 或兼容对象会抛出调用错误
                    disconnect()  # 新增代码+RealChrome断开: 只断开 Playwright 到 Chrome 的 CDP 连接；若没有这行代码，CDP 连接会残留或改用 close 误关真实 Chrome
                    disconnected_browser = True  # 新增代码+RealChrome断开: 标记已执行 CDP 断开；若没有这行代码，审计和返回无法说明实际动作
            except Exception:  # 新增代码+RealChrome断开: 忽略 CDP 断开异常继续清理本地引用；若没有这行代码，清理流程可能被异常中断
                pass  # 新增代码+RealChrome断开: 保持 except 分支语法完整；若没有这行代码，Python 会语法错误
        if was_real_chrome and close_browser and self.chrome_process is not None:  # 新增代码+RealChrome断开: 只有用户明确要求且存在本次 agent 启动进程时才终止 Chrome；若没有这行代码，默认可能误关用户真实 Chrome
            try:  # 新增代码+RealChrome断开: 捕获 terminate 异常以便状态仍能复位；若没有这行代码，进程已退出时会阻断断开返回
                self.chrome_process.terminate()  # 新增代码+RealChrome断开: 请求关闭本次 agent 启动的 Chrome；若没有这行代码，close_browser=true 时 agent 启动的 Chrome 可能残留
                terminated_process = True  # 新增代码+RealChrome断开: 标记已经请求终止进程；若没有这行代码，返回和审计无法确认 close_browser 生效
            except Exception:  # 新增代码+RealChrome断开: 容忍进程已经退出或 terminate 失败；若没有这行代码，清理会因为进程边界异常失败
                pass  # 新增代码+RealChrome断开: 保持 except 分支语法完整；若没有这行代码，Python 会语法错误
        if was_real_chrome and self.playwright is not None:  # 新增代码+RealChrome断开: 真实模式下没有独立 Chromium 会话需要保留时停止 Playwright；若没有这行代码，CDP driver 可能残留
            try:  # 新增代码+RealChrome断开: 捕获 stop 异常以便继续复位状态；若没有这行代码，driver stop 失败会留下旧引用
                self.playwright.stop()  # 新增代码+RealChrome断开: 停止 Playwright 驱动；若没有这行代码，真实模式断开后驱动进程可能仍在运行
            except Exception:  # 新增代码+RealChrome断开: 忽略 driver 停止异常；若没有这行代码，清理过程可能因二次停止而失败
                pass  # 新增代码+RealChrome断开: 保持 except 分支语法完整；若没有这行代码，Python 会语法错误
        if was_real_chrome:  # 新增代码+RealChrome断开: 只有真实模式断开才写审计和清理真实模式状态；若没有这行代码，无连接幂等调用会产生无意义审计
            try:  # 新增代码+RealChrome审计: 审计失败不能阻断安全断开；若没有这行代码，日志写入异常会让连接状态无法复位
                self.audit_logger.record("disconnect_real_chrome", {"close_browser": close_browser, "closed_browser": terminated_process, "closed_process": terminated_process, "terminated_process": terminated_process, "page_count": page_count})  # 新增代码+RealChrome审计: 只记录布尔开关和页面数量等摘要；若没有这行代码，高风险断开缺少最小留痕且可能写入敏感 profile 数据
            except Exception:  # 新增代码+RealChrome审计: 忽略审计写入异常继续复位；若没有这行代码，日志磁盘问题会破坏断开流程
                pass  # 新增代码+RealChrome审计: 保持 except 分支语法完整；若没有这行代码，Python 会语法错误
        if was_real_chrome:  # 新增代码+RealChrome断开: 真实模式断开后清空所有真实 Chrome 本地引用；若没有这行代码，后续工具可能误用已断开的对象
            self.browser = None  # 新增代码+RealChrome断开: 清空 CDP browser 引用；若没有这行代码，后续可能复用已断开的连接
            self.context = None  # 新增代码+RealChrome断开: 清空 context 引用但不调用 context.close；若没有这行代码，后续可能误用真实 profile 上下文
            self.pages = {}  # 新增代码+RealChrome断开: 清空页面映射但不关闭真实标签页；若没有这行代码，旧 page_id 会污染新会话
            self.current_page_id = None  # 新增代码+RealChrome断开: 清空当前页面 id；若没有这行代码，默认操作可能指向已断开的页面
            self.element_refs = {}  # 新增代码+RealChrome断开: 清空元素引用缓存；若没有这行代码，旧元素 id 会污染后续操作
            self.next_page_index = 1  # 新增代码+RealChrome断开: 重置页面编号游标；若没有这行代码，新会话 page_id 会延续旧真实页面编号
            self.real_chrome_endpoint = ""  # 新增代码+RealChrome断开: 清空 endpoint 摘要；若没有这行代码，状态工具会显示旧连接端点
            self.real_chrome_profile_summary = ""  # 新增代码+RealChrome断开: 清空 profile 摘要；若没有这行代码，用户可能误以为仍连接旧 profile
            self.chrome_process = None  # 新增代码+RealChrome断开: 清空本次 agent 启动进程引用；若没有这行代码，后续可能重复管理旧进程
            self.playwright = None  # 新增代码+RealChrome断开: 清空 Playwright driver 引用；若没有这行代码，后续可能误认为旧 driver 可用
            self.session_mode = "independent_chromium"  # 新增代码+RealChrome断开: 复位为默认独立 Chromium 模式；若没有这行代码，状态工具会误报仍连接真实 Chrome
        return {"was_real_chrome": was_real_chrome, "disconnected_browser": disconnected_browser, "terminated_process": terminated_process, "page_count": page_count}  # 新增代码+RealChrome断开: 返回机器可读断开摘要；若没有这行代码，调用方无法统一生成结果文本和测试断言

    def browser_disconnect_real_chrome(self, arguments: dict[str, Any]) -> str:  # 修改代码+RealChrome断开: 提供真实 Chrome 安全断开工具入口；若没有这行代码，tools/call 调用断开工具会失败或停留在临时桩
        close_browser = arguments.get("close_browser") is True  # 新增代码+RealChrome断开: 只有布尔 True 才允许关闭 agent 启动的 Chrome；若没有这行代码，字符串 true 等误传可能误关浏览器
        summary = self._disconnect_real_chrome_session(close_browser)  # 新增代码+RealChrome断开: 调用共享断开 helper；若没有这行代码，断开工具和 close_all 会出现不一致清理行为
        return "\n".join([  # 新增代码+RealChrome断开: 返回多行机器可读结果；若没有这行代码，MCP 调用方难以稳定解析断开状态
            "browser_disconnect_real_chrome",  # 新增代码+RealChrome断开: 输出工具名作为标题；若没有这行代码，用户不易确认结果来自断开工具
            "real_chrome_connected=false",  # 新增代码+RealChrome断开: 断开后统一报告未连接真实 Chrome；若没有这行代码，上层无法确认安全状态
            f"mode={self.session_mode}",  # 新增代码+RealChrome断开: 输出复位后的模式；若没有这行代码，用户无法确认已回到独立 Chromium
            f"closed_browser={str(summary['terminated_process']).lower()}",  # 新增代码+RealChrome断开: 说明本次是否终止 agent 启动的 Chrome；若没有这行代码，用户不知道 close_browser 是否生效
            f"pages={summary['page_count']}",  # 新增代码+RealChrome断开: 输出断开前页面数量；若没有这行代码，用户无法知道本次释放了多少本地页面映射
        ])  # 新增代码+RealChrome断开: 结束多行结果拼接；若没有这行代码，Python 列表和 join 语法不完整

    def browser_profile_status(self, arguments: dict[str, Any]) -> str:  # 修改代码+RealChrome状态: 提供完整只读 profile 状态工具入口；若没有这行代码，用户无法确认当前浏览器模式和真实 Chrome 风险状态
        _ = arguments  # 修改代码+RealChrome状态: 明确状态工具不读取输入参数；若没有这行代码，读者可能以为状态查询会读取敏感 profile 数据
        return "\n".join([  # 修改代码+RealChrome状态: 用固定字段返回当前安全状态；若没有这行代码，MCP client 收不到清晰状态摘要
            "browser_profile_status",  # 修改代码+RealChrome状态: 输出工具名作为状态标题；若没有这行代码，用户不易确认结果来自哪个工具
            f"mode={self.session_mode}",  # 修改代码+RealChrome状态: 从状态字段输出当前模式；若没有这行代码，连接真实 Chrome 后仍会误报默认模式
            f"real_chrome_connected={str(self.session_mode == 'real_chrome').lower()}",  # 修改代码+RealChrome状态: 根据当前模式输出连接布尔值；若没有这行代码，用户无法可靠判断真实 Chrome 是否连接
            f"chrome_started_by_agent={str(self.chrome_process is not None).lower()}",  # 新增代码+RealChrome状态: 输出是否存在 agent 启动进程；若没有这行代码，用户不知道 close_browser=true 是否有可关闭对象
            f"endpoint={self.real_chrome_endpoint}",  # 新增代码+RealChrome状态: 输出 endpoint 摘要或空值；若没有这行代码，用户无法核对当前 CDP 连接端点
            f"profile={self.real_chrome_profile_summary}",  # 新增代码+RealChrome状态: 输出 profile 摘要或空值且不读取敏感数据；若没有这行代码，用户无法确认连接来源
            f"pages={len(self.pages)}",  # 新增代码+RealChrome状态: 输出本地页面映射数量；若没有这行代码，用户不知道当前会话登记了多少页面
            f"最近安全拒绝：{self.last_safety_refusal}",  # 修改代码+RealChrome状态: 输出最近安全拒绝原因；若没有这行代码，状态工具无法解释安全拦截历史
        ])  # 修改代码+RealChrome状态: 结束多行状态拼接；若没有这行代码，Python 函数没有返回完整字符串

    def _browser_is_usable(self) -> bool:  # 新增代码+BrowserAutomation生命周期: 检查已有浏览器状态是否真的可用；若省略: 半初始化或已断开的浏览器会被错误复用
        if self.browser is None or self.context is None:  # 新增代码+BrowserAutomation生命周期: 浏览器或上下文缺任意一个都判定不可用；若省略: 后续访问缺失对象会报属性错误
            return False  # 新增代码+BrowserAutomation生命周期: 明确返回不可复用；若省略: ensure_browser 无法知道需要重启
        try:  # 新增代码+BrowserAutomation生命周期: 捕获 is_connected 或 pages 访问时的异常；若省略: 已损坏对象会让健康检查本身崩溃
            if not self.browser.is_connected():  # 新增代码+BrowserAutomation生命周期: 检查 Chromium 连接是否仍然存在；若省略: 已断开的 browser 可能被继续使用
                return False  # 新增代码+BrowserAutomation生命周期: 浏览器断开时判定不可用；若省略: 后续 new_page/goto 会失败得更晚
            _ = self.context.pages  # 新增代码+BrowserAutomation生命周期: 轻触上下文页面列表验证 context 仍可访问；若省略: 已关闭 context 可能漏过检查
        except Exception:  # 新增代码+BrowserAutomation生命周期: 容忍半坏对象抛出的异常；若省略: ensure_browser 不能安全清理半初始化状态
            return False  # 新增代码+BrowserAutomation生命周期: 检查异常时按不可用处理；若省略: 半坏状态可能继续污染后续工具
        return True  # 新增代码+BrowserAutomation生命周期: 浏览器和上下文均可访问时允许复用；若省略: 每次调用都会重启浏览器

    def ensure_browser(self) -> None:  # 新增代码+BrowserAutomation生命周期: 确保浏览器会话已经启动；若省略: 打开页面和标签页工具没有浏览器可用
        ensure_playwright_available()  # 新增代码+BrowserAutomation生命周期: 先检查 Playwright 依赖是否存在；若省略: 缺依赖时错误会更晚更难懂
        if self._browser_is_usable():  # 修改代码+BrowserAutomation生命周期: 只有浏览器连接和上下文都健康时才复用；若省略: 半初始化或断开的对象会被错误复用
            return  # 新增代码+BrowserAutomation生命周期: 已有会话时提前结束；若省略: 复用分支仍会继续创建新会话
        if self.playwright is not None or self.browser is not None or self.context is not None:  # 新增代码+BrowserAutomation生命周期: 发现残留对象时先清理半坏状态；若省略: 新会话可能叠在旧的半初始化对象上
            self.close_all()  # 新增代码+BrowserAutomation生命周期: 清掉半初始化或已断开的对象；若省略: 旧对象会继续占用资源并干扰重启
        try:  # 新增代码+BrowserAutomation生命周期: 包住启动流程以便失败时清理；若省略: launch/new_context 失败会留下半初始化状态
            self.playwright = sync_playwright().start()  # 新增代码+BrowserAutomation生命周期: 启动 Playwright 驱动；若省略: 无法调用 chromium.launch 创建浏览器
            self.browser = self.playwright.chromium.launch(headless=True)  # 新增代码+BrowserAutomation生命周期: 启动无头 Chromium；若省略: MCP 工具没有真实浏览器执行页面操作
            self.context = self.browser.new_context(accept_downloads=True)  # 新增代码+BrowserAutomation生命周期: 创建允许下载的浏览器上下文；若省略: 页面和下载事件没有隔离容器
            self.context.on("page", self._register_page)  # 新增代码+BrowserAutomation生命周期: 监听新页面并登记 page_id；若省略: 弹出的标签页无法被后续工具找到
        except Exception:  # 新增代码+BrowserAutomation生命周期: 启动任意阶段失败都进入清理；若省略: chromium.launch 或 new_context 失败后会残留半初始化对象
            self.close_all()  # 新增代码+BrowserAutomation生命周期: 清理启动失败留下的 Playwright/browser/context；若省略: 下一次调用可能复用坏状态
            raise  # 新增代码+BrowserAutomation生命周期: 重新抛出原始错误给调用方；若省略: 用户看不到真正的启动失败原因

    def _page_is_closed(self, page: Any) -> bool:  # 新增代码+BrowserAutomation标签页: 判断页面是否已关闭；若省略: 外部关闭页面后映射会继续指向失效 Page
        try:  # 新增代码+BrowserAutomation标签页: 捕获 is_closed 访问异常；若省略: 损坏页面对象会让状态清理失败
            return bool(page.is_closed())  # 新增代码+BrowserAutomation标签页: 使用 Playwright 的关闭状态；若省略: 无法可靠知道页面是否还能操作
        except Exception:  # 新增代码+BrowserAutomation标签页: 访问失败时当作已关闭；若省略: 异常页面可能继续被工具使用
            return True  # 新增代码+BrowserAutomation标签页: 异常页面视为不可用；若省略: current_page 可能返回坏页面

    def _forget_page(self, page_id: str) -> None:  # 新增代码+BrowserAutomation标签页: 从本地状态忘记一个页面；若省略: 页面关闭事件和失败清理会重复写移除逻辑
        self.pages.pop(page_id, None)  # 新增代码+BrowserAutomation标签页: 移除 page_id 到 Page 的映射；若省略: 已关闭页面会继续出现在列表中
        self.element_refs.pop(page_id, None)  # 新增代码+BrowserAutomation标签页: 移除该页快照元素引用；若省略: 旧元素 id 会污染后续页面操作
        if self.current_page_id == page_id:  # 新增代码+BrowserAutomation标签页: 只在忘记当前页时更新当前页；若省略: current_page_id 可能指向已删除页面
            self.current_page_id = next(reversed(self.pages), None) if self.pages else None  # 新增代码+BrowserAutomation标签页: 切到剩余最后页面或清空；若省略: 后续省略 page_id 的工具会找不到正确目标

    def _page_id_for_page(self, page: Any) -> str:  # 新增代码+BrowserAutomation标签页: 根据 Page 对象反查 page_id；若省略: 日志事件无法标记来自哪个页面
        for existing_page_id, existing_page in self.pages.items():  # 新增代码+BrowserAutomation标签页: 遍历已登记页面；若省略: 无法发现重复页面或找到事件来源
            if existing_page is page:  # 新增代码+BrowserAutomation标签页: 用对象身份判断是否同一个页面；若省略: 可能把同一页面登记成多个 id
                return existing_page_id  # 新增代码+BrowserAutomation标签页: 返回已存在的 page_id；若省略: 调用方拿不到稳定页面标识
        return ""  # 新增代码+BrowserAutomation标签页: 未找到时返回空字符串；若省略: 未登记事件会触发未定义返回值

    def safe_artifact_path(self, raw_name: Any, default_name: str, unique: bool = False) -> Path:  # 修改代码+BrowserAutomation路径: 统一生成 browser_artifacts 内安全产物路径并可选唯一化；若省略 unique: 下载同名文件会覆盖旧文件
        target_path = safe_browser_artifact_path(self.artifacts_dir, raw_name, default_name)  # 修改代码+BrowserSplit: 委托 browser.artifacts 生成基础安全路径；若没有这行代码，产物路径清洗规则仍不能独立测试复用。
        if unique:  # 修改代码+BrowserSplit: 只在下载等需要保留历史时生成不重名路径；若没有这行代码，同名下载仍可能覆盖旧文件。
            unique_path = target_path  # 修改代码+BrowserSplit: 从基础安全路径开始尝试；若没有这行代码，无法优先保留用户期望文件名。
            counter = 2  # 修改代码+BrowserSplit: 重名后缀从 2 开始，保持原有 name-2.ext 兼容格式；若没有这行代码，历史测试和用户习惯会变化。
            while unique_path.exists() or unique_path in self.reserved_artifact_paths:  # 修改代码+BrowserSplit: 文件已存在或已预留时继续递增；若没有这行代码，并发下载仍可能抢同一路径。
                unique_path = target_path.with_name(f"{target_path.stem}-{counter}{target_path.suffix}")  # 修改代码+BrowserSplit: 生成下一个候选唯一文件名；若没有这行代码，循环无法避开已存在文件。
                counter += 1  # 修改代码+BrowserSplit: 推进编号避免死循环；若没有这行代码，重名路径会让 while 一直卡住。
            return unique_path  # 修改代码+BrowserSplit: 返回确认可用的唯一路径；若没有这行代码，下载仍会使用已存在文件名。
        return target_path  # 修改代码+BrowserSplit: 非唯一场景直接返回基础安全路径；若没有这行代码，截图等场景拿不到 browser 层清洗结果。
        raw_text = str(raw_name or "").strip()  # 新增代码+BrowserAutomation路径: 把调用方传入的文件名转成去空白字符串；若省略: None 或空格会直接污染文件名判断
        fallback_text = str(default_name or "artifact").strip()  # 新增代码+BrowserAutomation路径: 准备默认文件名兜底；若省略: 用户传空名时没有稳定可写目标
        candidate_text = raw_text if raw_text else fallback_text  # 新增代码+BrowserAutomation路径: 优先使用用户文件名，空值时改用默认名；若省略: 空文件名会导致写目录或报错
        candidate_text = candidate_text.replace("\\", "_").replace("/", "_")  # 新增代码+BrowserAutomation路径: 把路径分隔符替换成下划线；若省略: ../ 或子目录片段可能影响写入位置
        safe_name = re.sub(r"[^A-Za-z0-9._ -]+", "_", candidate_text).strip(" .")  # 新增代码+BrowserAutomation路径: 只保留常见安全文件名字符；若省略: 控制字符或特殊字符可能造成跨平台写入问题
        if not safe_name or safe_name in {".", ".."}:  # 新增代码+BrowserAutomation路径: 检查清理后是否仍是空名或危险点目录；若省略: 文件名可能退化成当前目录或父目录
            safe_name = re.sub(r"[^A-Za-z0-9._ -]+", "_", fallback_text).strip(" .") or "artifact"  # 新增代码+BrowserAutomation路径: 再清理默认名并最终兜底 artifact；若省略: 默认名本身异常时仍会失败
        target_path = (self.artifacts_dir / safe_name).resolve()  # 新增代码+BrowserAutomation路径: 把安全文件名拼到产物目录并解析真实路径；若省略: 无法做越界校验
        artifacts_root = self.artifacts_dir.resolve()  # 新增代码+BrowserAutomation路径: 解析产物目录真实路径；若省略: 相对路径和符号链接边界无法比较
        try:  # 新增代码+BrowserAutomation路径: 用 relative_to 验证目标路径在产物目录内；若省略: 越界路径可能悄悄通过
            target_path.relative_to(artifacts_root)  # 新增代码+BrowserAutomation路径: 确认目标路径确实属于 browser_artifacts；若省略: 安全 helper 的核心保护不会执行
        except ValueError:  # 新增代码+BrowserAutomation路径: 捕获目标不在产物目录内的情况；若省略: 越界时会暴露底层异常或继续写错位置
            target_path = (artifacts_root / "artifact").resolve()  # 新增代码+BrowserAutomation路径: 越界时强制兜底到产物目录 artifact；若省略: 恶意文件名可能写到工作区外
        if unique:  # 新增代码+BrowserAutomation路径: 下载等需要保留历史的场景启用唯一文件名；若省略: 同名产物仍会覆盖旧文件
            unique_path = target_path  # 新增代码+BrowserAutomation路径: 从原始安全路径开始检查是否可用；若省略: 无法保留用户期望的首个文件名
            counter = 2  # 新增代码+BrowserAutomation路径: 重名时从 -2 后缀开始生成；若省略: 无法得到 name-2.ext 这类清晰命名
            while unique_path.exists() or unique_path in self.reserved_artifact_paths:  # 修改代码+BrowserAutomation路径: 文件已存在或已被下载预留时继续递增；若省略: 并发下载可能在落盘前抢到同一路径
                unique_path = target_path.with_name(f"{target_path.stem}-{counter}{target_path.suffix}")  # 新增代码+BrowserAutomation路径: 生成 name-2.ext、name-3.ext 形式路径；若省略: 用户难以区分重复下载文件
                counter += 1  # 新增代码+BrowserAutomation路径: 推进下一次重名编号；若省略: while 循环会一直检查同一个文件名
            target_path = unique_path  # 新增代码+BrowserAutomation路径: 使用确认不存在的唯一路径；若省略: helper 会返回已存在的原路径
        return target_path  # 修改代码+BrowserAutomation路径: 返回最终安全且必要时唯一的路径；若省略: 截图和下载方法拿不到可写文件位置

    def resolve_upload_path(self, raw_path: Any) -> Path:  # 新增代码+BrowserAutomation上传路径: 解析并校验上传文件只能来自 workspace；若省略: 页面上传可能读取工作区外敏感文件
        raw_text = str(raw_path or "").strip()  # 新增代码+BrowserAutomation上传路径: 读取用户传入路径并去掉边缘空白；若省略: 空格或 None 会造成难懂路径错误
        if not raw_text:  # 新增代码+BrowserAutomation上传路径: 检查上传路径不能为空；若省略: 空路径可能被解析成 workspace 目录
            raise RuntimeError("上传文件路径不能为空，请传入 workspace 内的真实文件路径。")  # 新增代码+BrowserAutomation上传路径: 用中文说明缺少路径；若省略: 新手用户不知道该传什么
        raw_candidate = Path(raw_text).expanduser()  # 新增代码+BrowserAutomation上传路径: 把字符串转成 Path 并展开用户目录；若省略: 后续无法统一判断绝对或相对路径
        candidate_path = raw_candidate if raw_candidate.is_absolute() else self.workspace / raw_candidate  # 新增代码+BrowserAutomation上传路径: 相对路径按 workspace 解析，绝对路径按原样解析；若省略: upload.txt 这种规格要求的相对路径不会生效
        upload_path = candidate_path.resolve()  # 新增代码+BrowserAutomation上传路径: 解析真实路径并跟随符号链接；若省略: 符号链接可能绕过 workspace 边界
        workspace_root = self.workspace.resolve()  # 新增代码+BrowserAutomation上传路径: 获取真实 workspace 根目录；若省略: 越界校验没有可信基准
        try:  # 新增代码+BrowserAutomation上传路径: 验证上传文件在 workspace 内；若省略: 绝对路径或 ../ 可读取外部文件
            upload_path.relative_to(workspace_root)  # 新增代码+BrowserAutomation上传路径: 确认真实上传路径属于 workspace；若省略: 安全边界无法落实
        except ValueError:  # 新增代码+BrowserAutomation上传路径: 捕获路径越界；若省略: 用户会看到英文底层异常
            raise RuntimeError("只能上传当前 workspace 内的文件，不能上传工作区外的路径。")  # 新增代码+BrowserAutomation上传路径: 用中文拒绝越界上传；若省略: 敏感文件可能被页面读取
        if not upload_path.exists():  # 新增代码+BrowserAutomation上传路径: 检查文件是否存在；若省略: Playwright 会在更底层报不友好的错误
            raise RuntimeError(f"上传文件不存在：{upload_path}")  # 新增代码+BrowserAutomation上传路径: 用中文说明缺失文件路径；若省略: 用户难以定位传错了哪个文件
        if not upload_path.is_file():  # 新增代码+BrowserAutomation上传路径: 检查目标必须是普通文件；若省略: 目录路径可能传给文件上传控件导致底层错误
            raise RuntimeError(f"上传路径必须是文件，不能是目录：{upload_path}")  # 新增代码+BrowserAutomation上传路径: 用中文拒绝目录上传；若省略: 用户不知道为什么目录不能上传
        return upload_path  # 新增代码+BrowserAutomation上传路径: 返回已验证的真实文件路径；若省略: 上传工具没有可传给 Playwright 的文件

    def _record_console(self, page: Any, message: Any) -> None:  # 新增代码+BrowserAutomation日志: 轻量记录 console 事件；若省略: 绑定 console 事件时会因为方法不存在报错
        self.console_logs.append({"page_id": self._page_id_for_page(page), "type": getattr(message, "type", ""), "text": getattr(message, "text", ""), "time": time.strftime("%Y-%m-%d %H:%M:%S")})  # 修改代码+BrowserAutomation日志: 保存页面、类型、文本和时间；若省略: browser_console 无法按规格展示来源和发生时间
        del self.console_logs[:-200]  # 修改代码+BrowserAutomation日志: 只保留最近 200 条；若省略: 长时间会话可能让日志列表无限增长

    def _record_request(self, page: Any, request: Any) -> None:  # 新增代码+BrowserAutomation网络: 轻量记录请求事件；若省略: 绑定 request 事件时会因为方法不存在报错
        self.network_logs.append({"page_id": self._page_id_for_page(page), "kind": "request", "method": getattr(request, "method", ""), "url": getattr(request, "url", ""), "resource_type": getattr(request, "resource_type", ""), "status": ""})  # 修改代码+BrowserAutomation网络: 保存请求摘要但不保存 body/header；若省略: browser_network 无法展示方法、资源类型和 URL
        del self.network_logs[:-400]  # 修改代码+BrowserAutomation网络: 只保留最近 400 条；若省略: 大页面会让网络列表不断膨胀

    def _record_response(self, page: Any, response: Any) -> None:  # 新增代码+BrowserAutomation网络: 轻量记录响应事件；若省略: 绑定 response 事件时会因为方法不存在报错
        request = getattr(response, "request", None)  # 新增代码+BrowserAutomation网络: 从响应对象取关联请求以补充方法和资源类型；若省略: 响应记录会缺少 method/resource_type
        self.network_logs.append({"page_id": self._page_id_for_page(page), "kind": "response", "method": getattr(request, "method", ""), "url": getattr(response, "url", ""), "resource_type": getattr(request, "resource_type", ""), "status": getattr(response, "status", "")})  # 修改代码+BrowserAutomation网络: 保存响应摘要但不保存 body/header；若省略: browser_network 无法展示响应状态和方法
        del self.network_logs[:-400]  # 修改代码+BrowserAutomation网络: 只保留最近 400 条；若省略: 响应记录可能无限占内存

    def _record_download(self, page: Any, download: Any) -> None:  # 新增代码+BrowserAutomation下载: 轻量记录下载事件；若省略: 绑定 download 事件时会因为方法不存在报错
        page_id = self._page_id_for_page(page)  # 新增代码+BrowserAutomation下载: 先保存下载所属页面 id；若省略: 保存失败记录也无法定位来源页面
        filename = str(getattr(download, "suggested_filename", "") or "").strip()  # 修改代码+BrowserAutomation下载: 读取浏览器建议文件名；若省略: 下载列表无法显示用户关心的文件名
        download_url = str(getattr(download, "url", "") or "")  # 新增代码+BrowserAutomation下载: 保存下载来源 URL；若省略: 成功或失败记录都缺少来源诊断
        event_time = time.strftime("%Y-%m-%d %H:%M:%S")  # 新增代码+BrowserAutomation下载: 保存事件发生时间；若省略: 下载失败记录无法判断发生顺序
        target_path_text = ""  # 新增代码+BrowserAutomation下载: 先准备可为空的保存路径文本；若省略: save_as 前失败时失败记录没有 path 字段
        target_path: Path | None = None  # 新增代码+BrowserAutomation下载: 记录本次下载预留的路径对象；若省略: finally 无法释放预留路径
        record_filename = filename or "download"  # 新增代码+BrowserAutomation下载: 准备成功或失败记录的文件名兜底；若省略: 保存失败时可能没有可读文件名
        error_text = ""  # 新增代码+BrowserAutomation下载: 准备错误文本字段，成功时保持为空；若省略: browser_downloads 难以区分成功和失败记录
        try:  # 新增代码+BrowserAutomation下载: 隔离下载保存异常，避免事件回调失败导致无诊断；若省略: save_as 异常会让下载记录完全丢失
            with self.download_lock:  # 修改代码+BrowserAutomation下载并发: 只锁住唯一命名和路径预留；若省略: 并发同名下载可能选择同一路径
                target_path = self.safe_artifact_path(filename, f"download-{int(time.time() * 1000)}.bin", unique=True)  # 修改代码+BrowserAutomation下载: 为下载生成唯一安全保存路径；若省略 unique=True: 同名下载会覆盖旧文件
                self.reserved_artifact_paths.add(target_path)  # 新增代码+BrowserAutomation下载并发: 在文件落盘前预留该路径；若省略: 第二个下载可能在文件存在前抢到同名路径
                target_path_text = str(target_path)  # 新增代码+BrowserAutomation下载: 保存目标路径字符串用于成功或失败记录；若省略: save_as 失败时不知道原计划写到哪里
                record_filename = target_path.name  # 新增代码+BrowserAutomation下载: 成功路径确定后使用最终唯一文件名；若省略: 下载列表可能显示原始文件名而不是落盘文件名
            download.save_as(target_path_text)  # 修改代码+BrowserAutomation下载: 把浏览器下载内容保存到唯一产物路径；若省略: browser_downloads 只能列事件但没有真实文件
        except Exception as error:  # 新增代码+BrowserAutomation下载: 捕获保存下载时的所有异常；若省略: 下载失败没有可见诊断且可能影响事件处理
            error_text = str(error)  # 新增代码+BrowserAutomation下载: 保存失败原因供 browser_downloads 输出；若省略: 失败记录缺少诊断细节
        finally:  # 新增代码+BrowserAutomation下载: 无论成功失败都释放预留并写入记录；若省略: 失败路径可能永久占用预留文件名或丢记录
            with self.download_lock:  # 新增代码+BrowserAutomation下载并发: 锁住预留释放和记录追加；若省略: 并发记录可能和唯一化检查互相踩踏
                if target_path is not None:  # 新增代码+BrowserAutomation下载并发: 只有成功预留过路径才释放；若省略: safe_artifact_path 失败时会访问空路径
                    self.reserved_artifact_paths.discard(target_path)  # 新增代码+BrowserAutomation下载并发: 下载结束后释放路径预留；若省略: 后续同名下载会一直跳过可用文件名
                self.downloads.append({"page_id": page_id, "filename": record_filename, "path": target_path_text, "url": download_url, "time": event_time, "error": error_text})  # 修改代码+BrowserAutomation下载: 记录成功或失败下载及错误文本；若省略: browser_downloads 无法展示本次下载状态
                del self.downloads[:-100]  # 修改代码+BrowserAutomation下载: 在锁内裁剪最近 100 条下载记录；若省略: 并发追加时下载记录可能长期堆积或顺序不稳

    def _register_page(self, page: Any) -> str:  # 新增代码+BrowserAutomation标签页: 登记 Playwright Page 并返回 page_id；若省略: 多页面工具无法定位页面
        existing_page_id = self._page_id_for_page(page)  # 新增代码+BrowserAutomation标签页: 先检查页面是否已登记；若省略: context 事件和手动登记会产生重复 id
        if existing_page_id:  # 新增代码+BrowserAutomation标签页: 如果已有 id 就走复用分支；若省略: 同一页面会被重复绑定和重复保存
            self.current_page_id = existing_page_id  # 新增代码+BrowserAutomation标签页: 把重复登记的页面设为当前页；若省略: 新打开页面可能没有成为当前操作目标
            return existing_page_id  # 新增代码+BrowserAutomation标签页: 返回已有 id；若省略: 调用方拿不到稳定页面标识
        page_id = f"page-{self.next_page_index}"  # 修改代码+BrowserAutomation标签页: 使用单调递增编号生成 page_id，避免关闭旧页后复用 id 覆盖仍存在页面；若省略: page-1 关闭后新页面可能再次生成 page-2 并覆盖旧 page-2
        self.next_page_index += 1  # 新增代码+BrowserAutomation标签页: 生成页面 id 后立刻推进下一个编号；若省略: 下一次新页面会重复使用同一个 page_id
        self.pages[page_id] = page  # 新增代码+BrowserAutomation标签页: 保存 page_id 到 Page 的映射；若省略: 后续工具无法找到该页面
        self.current_page_id = page_id  # 新增代码+BrowserAutomation标签页: 新登记页面自动成为当前页；若省略: 打开新页后工具可能仍操作旧页面
        page.on("close", lambda *args, page_id=page_id: self._forget_page(page_id))  # 新增代码+BrowserAutomation事件: 页面被外部关闭时自动忘记映射；若省略: browser_tabs/current_page 会看到失效页面
        page.on("console", lambda message, page_ref=page: self._record_console(page_ref, message))  # 新增代码+BrowserAutomation事件: 绑定 console 事件到轻量记录器；若省略: 后续无法积累控制台日志
        page.on("request", lambda request, page_ref=page: self._record_request(page_ref, request))  # 新增代码+BrowserAutomation事件: 绑定 request 事件到轻量记录器；若省略: 后续无法积累请求日志
        page.on("response", lambda response, page_ref=page: self._record_response(page_ref, response))  # 新增代码+BrowserAutomation事件: 绑定 response 事件到轻量记录器；若省略: 后续无法积累响应日志
        page.on("download", lambda download, page_ref=page: self._record_download(page_ref, download))  # 新增代码+BrowserAutomation事件: 绑定 download 事件到轻量记录器；若省略: 后续无法积累下载记录
        return page_id  # 新增代码+BrowserAutomation标签页: 把新 page_id 返回给调用方；若省略: browser_open/browser_tabs 无法告诉用户页面标识

    def current_page(self, page_id: str = "") -> tuple[str, Any]:  # 新增代码+BrowserAutomation标签页: 获取指定或当前页面；若省略: 多个工具会重复写页面查找逻辑
        wanted_page_id = page_id.strip() or (self.current_page_id or "")  # 新增代码+BrowserAutomation标签页: 空 page_id 时使用当前页；若省略: 用户省略 page_id 时工具不知道操作谁
        if not wanted_page_id or wanted_page_id not in self.pages:  # 新增代码+BrowserAutomation标签页: 校验页面 id 是否存在；若省略: 坏 id 会变成不清楚的 KeyError
            raise RuntimeError("找不到可用页面，请先调用 browser_open 打开页面，或调用 browser_tabs 查看并切换页面。")  # 新增代码+BrowserAutomation标签页: 给出中文修复建议；若省略: 新手用户不知道下一步该做什么
        page = self.pages[wanted_page_id]  # 修改代码+BrowserAutomation标签页: 先取出页面对象以便检查关闭状态；若省略: 可能直接返回已关闭页面
        if self._page_is_closed(page):  # 新增代码+BrowserAutomation标签页: 检查页面是否已经被外部关闭；若省略: 已关闭页面会在后续 title/goto/locator 时崩溃
            self._forget_page(wanted_page_id)  # 新增代码+BrowserAutomation标签页: 清理失效页面映射；若省略: 下次调用仍会遇到同一个坏页面
            raise RuntimeError("页面已经关闭，请调用 browser_tabs 查看可用页面，或调用 browser_open 打开新页面。")  # 新增代码+BrowserAutomation标签页: 用中文提示恢复方式；若省略: 用户不知道为何页面不可用
        return wanted_page_id, page  # 修改代码+BrowserAutomation标签页: 返回已确认可用的页面 id 和 Page 对象；若省略: 调用方无法同时拿到标识和对象

    def resolve_locator(self, page_id: str, page: Any, arguments: dict[str, Any]) -> Any:  # 新增代码+BrowserAutomation定位: 统一把 element_id、selector、text 或 label 解析成 Playwright locator；若省略: 点击和输入会各自重复且容易不一致
        raw_element_id = arguments.get("element_id")  # 修改代码+BrowserAutomation定位: 先读取原始 element_id 判断用户是否真的传了它；若省略: 缺省值会被 safe_int 下限夹成 1 并误用快照第一个元素
        has_element_id = raw_element_id is not None and str(raw_element_id).strip() != ""  # 修改代码+BrowserAutomation定位: 只有非空 element_id 才启用快照优先分支；若省略: selector 点击会被错误改成点击 element_id=1
        try:  # 修改代码+BrowserAutomation定位: 包住 element_id 的数字解析以便非法输入能报中文错误；若省略: 非数字 element_id 可能被静默改成 1
            parsed_element_id = int(str(raw_element_id).strip()) if has_element_id else 0  # 修改代码+BrowserAutomation定位: 仅在用户传入 element_id 时转整数；若省略: 未传 element_id 会被错误当成 1
        except (TypeError, ValueError, OverflowError):  # 修改代码+BrowserAutomation定位: 捕获非数字或超大数字解析失败；若省略: 用户会看到底层 Python 异常
            raise RuntimeError("element_id 必须是 1 到 10000 的数字，请重新调用 browser_snapshot 获取正确 id。")  # 修改代码+BrowserAutomation定位: 非法 element_id 给中文提示；若省略: 工具可能误点第一个元素
        if has_element_id and not 1 <= parsed_element_id <= 10000:  # 修改代码+BrowserAutomation定位: 明确拒绝 0、负数和超过上限的 element_id；若省略: 坏 id 会被夹成合法数字导致误操作
            raise RuntimeError("element_id 必须是 1 到 10000 的数字，请重新调用 browser_snapshot 获取正确 id。")  # 修改代码+BrowserAutomation定位: 越界 element_id 给中文提示；若省略: 0 或负数可能被错误改成 1
        element_id = safe_int(parsed_element_id, 0, 1, 10000) if has_element_id else 0  # 修改代码+BrowserAutomation定位: 合法 element_id 再用 safe_int 统一规范数值；若省略: 后续比较可能拿到非标准整数
        if element_id > 0:  # 新增代码+BrowserAutomation定位: 只有传入有效正数时才走快照元素分支；若省略: 默认 0 会错误触发元素查找
            for item in self.element_refs.get(page_id, []):  # 新增代码+BrowserAutomation定位: 遍历本页上次 browser_snapshot 保存的元素列表；若省略: element_id 无法映射回真实选择器
                if item.get("id") == element_id:  # 新增代码+BrowserAutomation定位: 找到 id 完全相同的快照元素；若省略: 可能用错其他元素
                    selector = str(item.get("selector", "") or "").strip()  # 新增代码+BrowserAutomation定位: 读取并清理快照保存的 CSS 选择器；若省略: 空格或 None 会让 locator 不稳定
                    if selector:  # 新增代码+BrowserAutomation定位: 只有选择器非空时才创建 locator；若省略: 空选择器会触发难懂的 Playwright 错误
                        return page.locator(selector).first  # 修改代码+BrowserAutomation定位: Python Playwright 的 first 是属性，返回匹配到的第一个元素；若省略: 点击输入无法通过快照 id 操作页面
            raise RuntimeError("找不到这个 element_id，请重新调用 browser_snapshot 获取最新元素列表。")  # 新增代码+BrowserAutomation定位: 快照元素不存在时提示重新快照；若省略: 用户不知道 element_id 已经过期
        selector = str(arguments.get("selector", "") or "").strip()  # 新增代码+BrowserAutomation定位: 读取并清理用户直接传入的 CSS 选择器；若省略: selector 参数无法生效
        if selector:  # 新增代码+BrowserAutomation定位: selector 非空时使用 CSS 定位；若省略: 有选择器也会继续误走文本分支
            return page.locator(selector).first  # 修改代码+BrowserAutomation定位: Python Playwright 的 first 是属性，返回 CSS 选择器匹配的第一个元素；若省略: 用户不能直接用 selector 操作页面
        label = str(arguments.get("label", "") or "").strip()  # 修改代码+BrowserAutomation定位: 单独读取表单 label，避免被 browser_type 的输入 text 抢走；若省略: label 定位输入框会失效
        exact = bool(arguments.get("exact"))  # 修改代码+BrowserAutomation定位: 提前读取 exact，供 label 和 text 两种定位共用；若省略: 用户无法控制精确匹配
        if label:  # 修改代码+BrowserAutomation定位: label 非空时优先按表单标签定位；若省略: {label, text} 输入会错误查找要输入的文本
            return page.get_by_label(label, exact=exact).first  # 修改代码+BrowserAutomation定位: 使用 Playwright 表单标签定位器；若省略: label 只能当普通页面文本，无法稳定定位输入框
        text = str(arguments.get("text", "") or "").strip()  # 修改代码+BrowserAutomation定位: label 缺失时才读取页面可见文本；若省略: 点击可见文字的能力不可用
        if text:  # 新增代码+BrowserAutomation定位: 只有文本非空时才使用文本定位；若省略: 空文本会匹配异常或错误元素
            return page.get_by_text(text, exact=exact).first  # 修改代码+BrowserAutomation定位: Python Playwright 的 first 是属性，返回文本匹配的第一个元素；若省略: 不能通过可见文字点击按钮或链接
        raise RuntimeError("缺少 element_id、selector、text 或 label，无法定位页面元素。")  # 新增代码+BrowserAutomation定位: 所有定位参数都缺失时给中文错误；若省略: 工具会用空目标继续执行并失败得更难懂

    def _format_tabs(self) -> str:  # 新增代码+BrowserAutomation标签页: 格式化标签页列表文本；若省略: browser_tabs list 分支没有统一输出
        for page_id, page in list(self.pages.items()):  # 新增代码+BrowserAutomation标签页: 列表前清理已经关闭的页面；若省略: browser_tabs 会显示失效 page
            if self._page_is_closed(page):  # 新增代码+BrowserAutomation标签页: 判断该页面是否已关闭；若省略: 外部关闭页面不会从列表移除
                self._forget_page(page_id)  # 新增代码+BrowserAutomation标签页: 忘记关闭页面并更新当前页；若省略: 当前页可能继续指向失效页面
        if not self.pages:  # 新增代码+BrowserAutomation标签页: 检查是否没有页面；若省略: 空列表时会返回空白难以理解
            return "当前没有打开的页面"  # 新增代码+BrowserAutomation标签页: 明确告诉用户没有页面；若省略: 用户不知道是否工具失败
        lines = ["当前打开的页面："]  # 新增代码+BrowserAutomation标签页: 创建输出标题；若省略: 多行列表缺少语义开头
        for page_id, page in self.pages.items():  # 新增代码+BrowserAutomation标签页: 遍历所有已登记页面；若省略: 无法逐个列出标签页
            state = "当前" if page_id == self.current_page_id else "后台"  # 新增代码+BrowserAutomation标签页: 标记当前页或后台页；若省略: 用户不知道默认操作对象
            title = page.title()  # 修改代码+BrowserAutomation标签页: 清理关闭页后直接读取可用页面标题；若省略: 用户看不到标签页标题
            url = page.url  # 修改代码+BrowserAutomation标签页: 清理关闭页后直接读取可用页面 URL；若省略: 用户看不到每个标签页位置
            lines.append(f"- {page_id} [{state}] 标题：{title} URL：{url}")  # 新增代码+BrowserAutomation标签页: 添加一行页面摘要；若省略: 标签页列表没有具体内容
        return "\n".join(lines)  # 新增代码+BrowserAutomation标签页: 合并多行文本返回；若省略: MCP 工具不能返回可读列表

    def _audit_browser_tool(self, tool_name: str, details: dict[str, Any]) -> None:  # 新增代码+RealChrome审计: 定义真实 Chrome 浏览器工具成功审计入口；若没有这行代码，高风险真实登录态工具成功调用没有统一安全留痕
        if self.session_mode != "real_chrome":  # 新增代码+RealChrome审计: 只在真实 Chrome 模式写 browser_tool 审计；若没有这行代码，普通独立 Chromium 测试和日常使用会产生不必要审计噪声
            return  # 新增代码+RealChrome审计: 非真实 Chrome 模式直接返回；若没有这行代码，后续仍可能写入审计文件
        blocked_keys = {"cookie", "cookies", "storage", "token", "password", "body", "header", "headers", "text", "value", "content"}  # 修改代码+RealChrome审计: 列出禁止写入审计的敏感键名但允许 script_allowed 这种布尔摘要；若没有这行代码，脚本全文、输入文本或敏感字段可能落入日志
        safe_details: dict[str, Any] = {}  # 新增代码+RealChrome审计: 准备只包含安全摘要的新字典；若没有这行代码，可能直接复用外部 details 导致敏感内容外泄
        for key, value in details.items():  # 新增代码+RealChrome审计: 遍历调用方给出的摘要字段；若没有这行代码，无法逐项过滤敏感键
            key_text = str(key)  # 新增代码+RealChrome审计: 把键名转成字符串便于检查；若没有这行代码，非字符串键可能让 lower 检查报错
            key_lower = key_text.lower()  # 新增代码+RealChrome审计: 使用小写键名做不区分大小写的敏感匹配；若没有这行代码，Token 或 Password 这类大小写变化可能绕过过滤
            if key_lower == "script" or any(blocked_key in key_lower for blocked_key in blocked_keys):  # 修改代码+RealChrome审计: 跳过脚本全文字段和任何疑似 cookie、token、正文或 header 的字段；若没有这行代码，审计可能保存不该保存的隐私数据
                continue  # 新增代码+RealChrome审计: 丢弃敏感字段继续处理其他摘要；若没有这行代码，过滤条件命中后仍会写入风险字段
            if isinstance(value, (str, int, float, bool)) or value is None:  # 新增代码+RealChrome审计: 只允许简单标量进入审计摘要；若没有这行代码，复杂对象可能带出页面、请求或文件内容
                safe_details[key_text] = value  # 新增代码+RealChrome审计: 保存通过过滤的安全摘要字段；若没有这行代码，审计会缺少 page_id/count/action 等排查信息
            else:  # 新增代码+RealChrome审计: 复杂值进入兜底分支；若没有这行代码，列表或对象可能被直接写入
                safe_details[key_text] = type(value).__name__  # 新增代码+RealChrome审计: 复杂值只记录类型名不记录内容；若没有这行代码，复杂值内部敏感内容可能泄露
        try:  # 新增代码+RealChrome审计: 捕获审计写入异常保护主流程；若没有这行代码，日志磁盘错误会导致正常浏览器工具失败
            self.audit_logger.record("browser_tool", {"tool_name": tool_name, "details": safe_details})  # 新增代码+RealChrome审计: 写入统一 browser_tool 事件和安全摘要；若没有这行代码，真实 Chrome 成功操作没有最小可追踪记录
        except Exception:  # 新增代码+RealChrome审计: 审计失败时进入容错分支；若没有这行代码，audit_logger.record 抛错会向用户暴露为工具失败
            pass  # 新增代码+RealChrome审计: 忽略审计失败并保护浏览器主流程；若没有这行代码，except 分支语法不完整且无法继续

    def browser_open(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation骨架: 声明打开网页方法返回文本；若省略: 后续实现返回类型和协议包装不一致
        url = str(arguments.get("url", "")).strip()  # 修改代码+BrowserAutomation打开: 读取并清理 URL 参数；若省略: 空格或非字符串输入会让 page.goto 行为不稳定
        if not (url.startswith("http://") or url.startswith("https://")):  # 修改代码+BrowserAutomation打开: 只允许 http/https 页面；若省略: file/javascript 等地址可能带来安全和测试不一致问题
            raise RuntimeError("browser_open 只支持 http:// 或 https:// URL。")  # 修改代码+BrowserAutomation打开: 返回中文 URL 限制错误；若省略: 用户不知道为什么打不开本地路径或其他协议
        timeout_ms = safe_int(arguments.get("timeout_ms", DEFAULT_TIMEOUT_MS), DEFAULT_TIMEOUT_MS, 1, MAX_TIMEOUT_MS)  # 修改代码+BrowserAutomation打开: 解析并限制打开页面超时；若省略: 坏参数可能导致无限等待或直接报错
        self.ensure_browser()  # 修改代码+BrowserAutomation打开: 确保 Chromium 会话存在；若省略: 没有浏览器上下文可创建页面
        created_new_page = False  # 新增代码+BrowserAutomation打开: 记录本次是否新建页面以便导航失败时清理；若省略: 新页 goto 失败会留下空白页
        if arguments.get("new_tab", False) is True or self.current_page_id is None:  # 修改代码+BrowserAutomation打开: 只有真正 boolean True 或没有当前页时才创建新页面；若省略: 字符串 "false" 会被误当成新标签开关
            page = self.context.new_page()  # 修改代码+BrowserAutomation打开: 在当前上下文中新建页面；若省略: 无法打开首个或新的标签页
            page_id = self._register_page(page)  # 修改代码+BrowserAutomation打开: 登记新页面并获取 page_id；若省略: 后续工具无法定位该页面
            created_new_page = True  # 新增代码+BrowserAutomation打开: 标记本次页面由 browser_open 创建；若省略: 失败分支不知道是否可以安全关闭该页
        else:  # 修改代码+BrowserAutomation打开: 有当前页且不强制新标签时走复用分支；若省略: 每次打开都会产生新标签页
            page_id, page = self.current_page()  # 修改代码+BrowserAutomation打开: 获取当前页面用于复用导航；若省略: 无法在当前标签页打开新 URL
        try:  # 新增代码+BrowserAutomation打开: 捕获导航失败以便只清理本次新建页；若省略: 新建页失败会残留空白标签
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)  # 修改代码+BrowserAutomation打开: 导航到目标 URL 并等待 DOM 就绪；若省略: 页面不会真正打开
        except Exception:  # 新增代码+BrowserAutomation打开: 导航超时或失败时进入清理分支；若省略: 失败状态会污染页面集合
            if created_new_page:  # 新增代码+BrowserAutomation打开: 仅关闭本次新建页面，复用当前页时保留原页面；若省略: 复用页面失败可能误删用户已有页面
                try:  # 新增代码+BrowserAutomation打开: 容忍关闭失败；若省略: 原始 goto 错误可能被关闭错误掩盖
                    page.close()  # 新增代码+BrowserAutomation打开: 关闭导航失败的新页面；若省略: 工具失败后会留下 about:blank
                except Exception:  # 新增代码+BrowserAutomation打开: 忽略关闭异常继续忘记本地映射；若省略: 已关闭页面会造成二次错误
                    pass  # 新增代码+BrowserAutomation打开: 保持清理分支语法完整；若省略: except 分支无语句会语法错误
                self._forget_page(page_id)  # 新增代码+BrowserAutomation打开: 移除失败新页映射和元素引用；若省略: 后续标签页列表会显示失败空白页
            raise  # 新增代码+BrowserAutomation打开: 重新抛出导航错误；若省略: 调用方会误以为页面打开成功
        self.current_page_id = page_id  # 修改代码+BrowserAutomation打开: 导航成功后更新当前页；若省略: 后续工具可能操作旧页面
        self._audit_browser_tool("browser_open", {"page_id": page_id, "action": "open", "new_page": created_new_page})  # 新增代码+RealChrome审计: 成功打开页面后只记录 page_id、动作和是否新页；若没有这行代码，真实 Chrome 打开动作缺少安全摘要审计
        return f"browser_open 成功\npage_id={page_id}\n标题：{page.title()}\nURL：{page.url}"  # 修改代码+BrowserAutomation打开: 返回成功摘要；若省略: 调用方不知道打开结果和 page_id

    def browser_snapshot(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation骨架: 声明页面快照方法返回文本；若省略: 后续实现返回类型和协议包装不一致
        page_id, page = self.current_page(str(arguments.get("page_id", "") or ""))  # 修改代码+BrowserAutomation快照: 获取指定或当前页面；若省略: 快照工具不知道读取哪个页面
        max_text_chars = safe_int(arguments.get("max_text_chars", DEFAULT_MAX_CHARS), DEFAULT_MAX_CHARS, 1, MAX_RESULT_CHARS)  # 修改代码+BrowserAutomation快照: 解析正文最大字符数；若省略: 大页面可能返回过长文本
        max_elements = safe_int(arguments.get("max_elements", 30), 30, 1, 200)  # 修改代码+BrowserAutomation快照: 解析可交互元素最大数量；若省略: 表单复杂页面可能输出太多元素
        body_text = ""  # 修改代码+BrowserAutomation快照: 默认正文为空以兼容没有 body 或读取失败的页面；若省略: 无 body 页面会让 snapshot 崩溃
        try:  # 新增代码+BrowserAutomation快照: 捕获 body 查询和读取异常；若省略: inner_text 失败会中断整个快照
            body_locator = page.locator("body")  # 新增代码+BrowserAutomation快照: 创建 body 定位器；若省略: 无法判断页面是否有 body
            if body_locator.count() > 0:  # 新增代码+BrowserAutomation快照: 只有存在 body 时才读取文本；若省略: 无 body 页面会抛错
                body_text = body_locator.inner_text(timeout=DEFAULT_TIMEOUT_MS)  # 修改代码+BrowserAutomation快照: 读取 body 可见文本；若省略: 快照没有正文摘要
        except Exception:  # 新增代码+BrowserAutomation快照: body 读取失败时继续返回空正文；若省略: 页面小异常会导致快照整体失败
            body_text = ""  # 新增代码+BrowserAutomation快照: 失败时保持空正文；若省略: body_text 可能未定义
        body_summary, body_clipped = clip_text(normalize_spaces(body_text), max_text_chars)  # 修改代码+BrowserAutomation快照: 归一化空白并截断正文；若省略: 输出可能冗长且换行混乱
        elements = page.evaluate("() => { const escapeCss = (value) => { if (window.CSS && CSS.escape) { return CSS.escape(String(value)); } return String(value).replace(/[^a-zA-Z0-9_-]/g, (ch) => '\\\\' + ch.charCodeAt(0).toString(16) + ' '); }; const nthOfType = (node) => { const tag = node.tagName.toLowerCase(); const siblings = Array.from(node.parentElement ? node.parentElement.children : []).filter((child) => child.tagName === node.tagName); return `${tag}:nth-of-type(${siblings.indexOf(node) + 1})`; }; const selectorFor = (node) => { if (node.id) { return `${node.tagName.toLowerCase()}#${escapeCss(node.id)}`; } const parts = []; let current = node; while (current && current.nodeType === 1 && current !== document.documentElement) { if (current.id) { parts.unshift(`${current.tagName.toLowerCase()}#${escapeCss(current.id)}`); break; } parts.unshift(nthOfType(current)); current = current.parentElement; } return parts.join(' > '); }; return Array.from(document.querySelectorAll('a,button,input,textarea,select,[role=\"button\"],[role=\"link\"],[contenteditable=\"true\"]')).slice(0, 200).map((el, index) => { const tag = el.tagName.toLowerCase(); const text = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || el.getAttribute('placeholder') || el.name || '').replace(/\\s+/g, ' ').trim(); const rect = el.getBoundingClientRect(); const style = window.getComputedStyle(el); return { id: index + 1, tag, label: text, selector: selectorFor(el), visible: !!(rect.width && rect.height && style.visibility !== 'hidden' && style.display !== 'none') }; }); }")  # 修改代码+BrowserAutomation快照: 生成带祖先路径的 selector 并兼容没有 CSS.escape 的页面；若省略: 多个同类元素可能得到不准确的全页 nth-of-type 选择器
        elements = elements[:max_elements]  # 修改代码+BrowserAutomation快照: 按用户参数限制元素数量；若省略: JS 最多 200 条仍可能超出期望
        self.element_refs[page_id] = elements  # 修改代码+BrowserAutomation快照: 保存本页元素引用；若省略: 后续 Task 的点击输入无法复用快照 id
        element_lines = [f"{item.get('id')}. <{item.get('tag')}> label={item.get('label')!r} selector={item.get('selector')} visible={item.get('visible')}" for item in elements]  # 修改代码+BrowserAutomation快照: 格式化元素列表；若省略: 返回内容难以阅读和断言
        elements_text = "\n".join(element_lines) if element_lines else "未找到可交互元素"  # 修改代码+BrowserAutomation快照: 处理有无元素两种输出；若省略: 空元素时用户会看到空白区域
        clipped_text = "已截断" if body_clipped else "未截断"  # 修改代码+BrowserAutomation快照: 标注正文是否被截断；若省略: 用户不知道摘要是否完整
        return f"browser_snapshot 成功\n标题：{page.title()}\nURL：{page.url}\n正文截断状态：{clipped_text}\n正文摘要：{body_summary}\n可交互元素：\n{elements_text}"  # 修改代码+BrowserAutomation快照: 返回快照摘要和元素列表；若省略: 调用方无法读取页面状态

    def browser_click(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation点击: 声明点击方法返回文本；若省略: MCP 分发后无法执行点击
        page_id, page = self.current_page(str(arguments.get("page_id", "") or ""))  # 修改代码+BrowserAutomation点击: 获取指定或当前页面；若省略: 点击不知道该操作哪个标签页
        timeout_ms = safe_int(arguments.get("timeout_ms", DEFAULT_TIMEOUT_MS), DEFAULT_TIMEOUT_MS, 1, MAX_TIMEOUT_MS)  # 修改代码+BrowserAutomation点击: 解析点击等待超时并限制范围；若省略: 坏超时参数会导致等待异常或过久
        locator = self.resolve_locator(page_id, page, arguments)  # 新增代码+BrowserAutomation点击: 把用户目标解析成页面元素定位器；若省略: click 没有可点击对象
        locator.click(timeout=timeout_ms)  # 新增代码+BrowserAutomation点击: 执行真实点击并按超时等待元素可点；若省略: 工具只会假装成功但页面没有变化
        self._audit_browser_tool("browser_click", {"page_id": page_id, "action": "click", "has_element_id": bool(str(arguments.get("element_id", "") or "").strip()), "has_selector": bool(str(arguments.get("selector", "") or "").strip()), "has_label": bool(str(arguments.get("label", "") or "").strip())})  # 新增代码+RealChrome审计: 点击成功后只记录目标类型布尔摘要；若没有这行代码，真实 Chrome 点击动作缺少审计或可能误写定位原文
        return f"browser_click 成功\n点击完成\npage_id={page_id}\nURL：{page.url}"  # 修改代码+BrowserAutomation点击: 返回点击成功、页面 id 和当前 URL；若省略: 调用方不知道点击是否完成

    def browser_type(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation输入: 声明输入方法返回文本；若省略: MCP 分发后无法执行输入
        page_id, page = self.current_page(str(arguments.get("page_id", "") or ""))  # 修改代码+BrowserAutomation输入: 获取指定或当前页面；若省略: 输入不知道该操作哪个标签页
        text = str(arguments.get("text", "") or "")  # 新增代码+BrowserAutomation输入: 读取要输入的文本并保证是字符串；若省略: fill 可能收到 None 或非字符串而报错
        if text == "":  # 修改代码+BrowserAutomation输入: 运行时拒绝空输入文本；若省略: 空 text 会让输入工具看似成功但没有输入内容
            raise RuntimeError("browser_type 缺少非空 text 参数。")  # 修改代码+BrowserAutomation输入: 用中文说明 text 不能为空；若省略: 新手用户不知道为什么页面没有变化
        timeout_ms = safe_int(arguments.get("timeout_ms", DEFAULT_TIMEOUT_MS), DEFAULT_TIMEOUT_MS, 1, MAX_TIMEOUT_MS)  # 修改代码+BrowserAutomation输入: 解析输入等待超时并限制范围；若省略: 坏超时参数会导致等待异常或过久
        clear = bool(arguments.get("clear", True))  # 新增代码+BrowserAutomation输入: 默认输入前清空旧内容；若省略: 新文本可能追加到旧文本导致测试和用户预期不一致
        has_explicit_target = any(str(arguments.get(name, "") or "").strip() for name in ("element_id", "selector", "label"))  # 修改代码+BrowserAutomation输入: 只把 element_id/selector/label 当成输入目标，避免把 text 误当定位文本；若省略: 只传 text 时会错误查找页面文字
        if has_explicit_target:  # 修改代码+BrowserAutomation输入: 有明确目标时才使用 locator 操作输入框；若省略: 指定输入框的调用无法定位目标元素
            locator = self.resolve_locator(page_id, page, arguments)  # 修改代码+BrowserAutomation输入: 把显式目标解析成输入框定位器；若省略: fill/type 没有目标元素
            if clear:  # 修改代码+BrowserAutomation输入: clear=True 时覆盖目标输入框内容；若省略: 旧内容可能残留并污染本次输入
                locator.fill(text, timeout=timeout_ms)  # 修改代码+BrowserAutomation输入: 使用 fill 覆盖目标输入框；若省略: 页面不会真正收到用户文本
            else:  # 修改代码+BrowserAutomation输入: clear=False 时追加到目标输入框；若省略: 用户无法表达在已有内容后继续输入
                locator.type(text, timeout=timeout_ms)  # 修改代码+BrowserAutomation输入: 使用 type 追加文本并触发键盘输入事件；若省略: clear=False 仍会覆盖原内容
        else:  # 修改代码+BrowserAutomation输入: 没有显式目标时改用当前焦点输入；若省略: 只传 text 的调用会错误把 text 当定位文本
            if clear:  # 修改代码+BrowserAutomation输入: 无显式目标且 clear=True 时清空当前焦点内容；若省略: 当前焦点输入会保留旧内容
                page.keyboard.press("Control+A")  # 修改代码+BrowserAutomation输入: 选中当前焦点里的已有文本；若省略: 无目标输入无法先清空
            page.keyboard.type(text)  # 修改代码+BrowserAutomation输入: 无显式目标时向当前焦点键入文本；若省略: browser_type 只传 text 时不会输入到焦点元素
        self._audit_browser_tool("browser_type", {"page_id": page_id, "action": "type", "character_count": len(text), "clear": clear, "has_explicit_target": has_explicit_target})  # 新增代码+RealChrome审计: 输入成功后只记录字符数和目标是否显式；若没有这行代码，真实 Chrome 输入动作缺少审计或可能泄露用户输入原文
        return f"browser_type 成功\n输入完成\npage_id={page_id}\n字符数：{len(text)}"  # 修改代码+BrowserAutomation输入: 返回输入成功、页面 id 和字符数；若省略: 调用方不知道输入了多少内容

    def browser_press_key(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation按键: 声明按键方法返回文本；若省略: MCP 分发后无法执行键盘操作
        page_id, page = self.current_page(str(arguments.get("page_id", "") or ""))  # 修改代码+BrowserAutomation按键: 获取指定或当前页面；若省略: 按键不知道该发送到哪个标签页
        key = str(arguments.get("key", "") or "").strip()  # 新增代码+BrowserAutomation按键: 读取并清理按键名称；若省略: 空格或 None 会传给 Playwright 造成难懂错误
        if not key:  # 新增代码+BrowserAutomation按键: 检查按键名称不能为空；若省略: 空按键会让 Playwright 报低层错误
            raise RuntimeError("browser_press_key 缺少非空 key 参数。")  # 新增代码+BrowserAutomation按键: 用中文说明缺少 key；若省略: 新手用户不知道该传什么
        page.keyboard.press(key)  # 新增代码+BrowserAutomation按键: 发送真实键盘按键到当前页面；若省略: 页面不会触发键盘事件
        self._audit_browser_tool("browser_press_key", {"page_id": page_id, "action": "press_key", "key_present": True})  # 新增代码+RealChrome审计: 按键成功后只记录有按键动作不记录具体键值；若没有这行代码，真实 Chrome 键盘操作缺少审计或可能暴露输入意图
        return f"browser_press_key 成功\n按键完成：{key}\npage_id={page_id}\nURL：{page.url}"  # 修改代码+BrowserAutomation按键: 返回按键成功、按键名和页面信息；若省略: 调用方不知道按键是否完成

    def browser_wait(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation等待: 声明等待方法返回文本；若省略: MCP 分发后无法等待页面变化
        page_id, page = self.current_page(str(arguments.get("page_id", "") or ""))  # 修改代码+BrowserAutomation等待: 获取指定或当前页面；若省略: 等待不知道该观察哪个标签页
        timeout_ms = safe_int(arguments.get("timeout_ms", DEFAULT_TIMEOUT_MS), DEFAULT_TIMEOUT_MS, 1, MAX_TIMEOUT_MS)  # 修改代码+BrowserAutomation等待: 解析等待上限并限制范围；若省略: 坏超时参数会导致等待异常或过久
        milliseconds = safe_int(arguments.get("milliseconds", 0), 0, 0, MAX_TIMEOUT_MS)  # 新增代码+BrowserAutomation等待: 读取固定等待毫秒数并限制范围；若省略: milliseconds 等待参数不会生效
        selector = str(arguments.get("selector", "") or "").strip()  # 新增代码+BrowserAutomation等待: 读取要等待出现的 CSS 选择器；若省略: selector 条件无法生效
        text = str(arguments.get("text", "") or "").strip()  # 新增代码+BrowserAutomation等待: 读取要等待出现的可见文本；若省略: text 条件无法生效
        url_contains = str(arguments.get("url_contains", "") or "").strip()  # 新增代码+BrowserAutomation等待: 读取 URL 需要包含的片段；若省略: URL 条件无法生效
        load_state = str(arguments.get("load_state", "") or "").strip()  # 新增代码+BrowserAutomation等待: 读取页面加载状态条件；若省略: load_state 条件无法生效
        checks: list[str] = []  # 新增代码+BrowserAutomation等待: 收集实际完成的等待检查说明；若省略: 返回结果无法告诉用户等待了什么
        if milliseconds > 0:  # 新增代码+BrowserAutomation等待: 固定等待大于 0 时执行；若省略: 传入 milliseconds 也不会暂停
            page.wait_for_timeout(milliseconds)  # 新增代码+BrowserAutomation等待: 让页面等待指定毫秒数；若省略: 动画或异步任务可能还没完成
            checks.append(f"固定等待 {milliseconds} 毫秒")  # 新增代码+BrowserAutomation等待: 记录固定等待已完成；若省略: 返回文本缺少等待内容说明
        if selector:  # 新增代码+BrowserAutomation等待: selector 非空时等待元素出现；若省略: 元素等待条件会被忽略
            page.locator(selector).first.wait_for(timeout=timeout_ms)  # 修改代码+BrowserAutomation等待: Python Playwright 的 first 是属性，等待第一个匹配元素出现；若省略: 后续操作可能抢在元素出现前执行
            checks.append(f"selector={selector}")  # 新增代码+BrowserAutomation等待: 记录 selector 检查已完成；若省略: 返回文本无法确认等的是哪个选择器
        if text:  # 新增代码+BrowserAutomation等待: text 非空时等待可见文本出现；若省略: 文本等待条件会被忽略
            page.get_by_text(text).first.wait_for(timeout=timeout_ms)  # 修改代码+BrowserAutomation等待: Python Playwright 的 first 是属性，等待第一个匹配文本出现；若省略: 后续断言可能读不到异步文本
            checks.append(f"text={text}")  # 新增代码+BrowserAutomation等待: 记录文本检查已完成；若省略: 返回文本无法确认等的是哪段文字
        if url_contains:  # 新增代码+BrowserAutomation等待: URL 片段非空时等待当前地址包含它；若省略: 页面跳转等待条件会被忽略
            deadline = time.time() + (timeout_ms / 1000)  # 新增代码+BrowserAutomation等待: 计算轮询截止时间；若省略: URL 等待可能无限循环或立刻结束
            while url_contains not in page.url:  # 新增代码+BrowserAutomation等待: 持续检查当前 URL 是否包含目标片段；若省略: 不能确认跳转是否完成
                if time.time() >= deadline:  # 新增代码+BrowserAutomation等待: 检查是否已经超过等待上限；若省略: URL 等待可能一直卡住
                    raise RuntimeError(f"等待 URL 包含 {url_contains} 超时，当前 URL：{page.url}")  # 新增代码+BrowserAutomation等待: URL 超时时给中文错误和当前地址；若省略: 用户不知道实际停在哪个 URL
                page.wait_for_timeout(100)  # 新增代码+BrowserAutomation等待: 每次轮询短暂暂停避免 CPU 空转；若省略: 循环会占满处理器
            checks.append(f"url_contains={url_contains}")  # 新增代码+BrowserAutomation等待: 记录 URL 检查已完成；若省略: 返回文本无法确认等的是哪个 URL 片段
        if load_state:  # 新增代码+BrowserAutomation等待: load_state 非空时等待页面加载状态；若省略: 加载状态等待条件会被忽略
            page.wait_for_load_state(load_state, timeout=timeout_ms)  # 新增代码+BrowserAutomation等待: 等待 Playwright 指定加载状态；若省略: 页面资源可能尚未到达用户要求状态
            checks.append(f"load_state={load_state}")  # 新增代码+BrowserAutomation等待: 记录加载状态检查已完成；若省略: 返回文本无法确认等待了哪种状态
        if not checks:  # 新增代码+BrowserAutomation等待: 没有任何等待条件时给出清楚错误；若省略: 工具会什么都不做却返回成功
            raise RuntimeError("browser_wait 缺少 milliseconds、selector、text、url_contains 或 load_state 参数。")  # 新增代码+BrowserAutomation等待: 用中文说明需要至少一个等待条件；若省略: 新手用户不知道该怎么调用
        checks_text = "；".join(checks)  # 新增代码+BrowserAutomation等待: 把多种等待检查合并成可读文本；若省略: 返回结果难以阅读
        return f"browser_wait 成功\npage_id={page_id}\nURL：{page.url}\n文本检查：{checks_text}"  # 修改代码+BrowserAutomation等待: 返回等待成功、页面 id、URL 和检查内容；若省略: 调用方不知道等待结果

    def browser_screenshot(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation骨架: 声明截图方法返回文本；若省略: 后续实现返回类型和协议包装不一致
        page_id, page = self.current_page(str(arguments.get("page_id", "") or ""))  # 修改代码+BrowserAutomation截图: 获取指定或当前页面；若省略: 截图不知道该截哪个标签页
        default_name = f"screenshot-{int(time.time() * 1000)}.png"  # 新增代码+BrowserAutomation截图: 生成默认 PNG 文件名；若省略: 用户不传 filename 时没有稳定输出文件
        target_path = self.safe_artifact_path(arguments.get("filename", ""), default_name)  # 新增代码+BrowserAutomation截图: 把用户文件名清理成产物目录内路径；若省略: 截图可能写到 browser_artifacts 外
        if target_path.suffix.lower() != ".png":  # 新增代码+BrowserAutomation截图: 检查最终文件名是否带 PNG 后缀；若省略: 保存 PNG 时可能使用误导扩展名
            target_path = target_path.with_name(f"{target_path.name}.png")  # 新增代码+BrowserAutomation截图: 没有 .png 时补上后缀；若省略: 用户难以识别截图文件格式
        full_page = bool(arguments.get("full_page", False))  # 新增代码+BrowserAutomation截图: 读取是否整页截图；若省略: full_page 参数不会生效
        page.screenshot(path=str(target_path), full_page=full_page)  # 新增代码+BrowserAutomation截图: 调用 Playwright 保存真实 PNG 截图；若省略: browser_screenshot 只会返回文本而没有图片文件
        self._audit_browser_tool("browser_screenshot", {"page_id": page_id, "action": "screenshot", "file_present": True, "full_page": full_page})  # 新增代码+RealChrome审计: 截图成功后只记录文件存在和整页开关；若没有这行代码，真实 Chrome 截图动作缺少安全摘要审计
        return f"browser_screenshot 成功\npage_id={page_id}\n文件：{target_path}\n目录：{self.artifacts_dir}"  # 修改代码+BrowserAutomation截图: 返回包含绝对路径和 browser_artifacts 目录的结果；若省略: 用户找不到截图产物

    def browser_tabs(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation骨架: 声明标签页方法返回文本；若省略: 后续实现返回类型和协议包装不一致
        action = str(arguments.get("action", "list") or "list").strip().lower()  # 修改代码+BrowserAutomation标签页: 读取标签页动作并默认 list；若省略: 空 action 会导致分支不稳定
        if action == "new":  # 修改代码+BrowserAutomation标签页: 处理新建标签页动作；若省略: 用户无法通过 browser_tabs 创建页面
            url = str(arguments.get("url", "") or "").strip()  # 修改代码+BrowserAutomation标签页: 创建页面前读取可选 URL；若省略: 非法 URL 会在空白页创建后才发现
            if url and not (url.startswith("http://") or url.startswith("https://")):  # 修改代码+BrowserAutomation标签页: 创建页面前校验 URL 协议；若省略: file:// 等非法 URL 会留下空白页
                raise RuntimeError("browser_tabs new 只支持 http:// 或 https:// URL。")  # 修改代码+BrowserAutomation标签页: 非法 URL 直接报中文错误；若省略: 用户不知道支持哪些协议
            self.ensure_browser()  # 修改代码+BrowserAutomation标签页: 确保浏览器会话存在；若省略: 无上下文可新建标签页
            page = self.context.new_page()  # 修改代码+BrowserAutomation标签页: 新建一个空页面；若省略: new 动作不会产生标签页
            page_id = self._register_page(page)  # 修改代码+BrowserAutomation标签页: 登记新页面并设为当前页；若省略: 新标签页无法被后续工具使用
            if url:  # 修改代码+BrowserAutomation标签页: 只有传入 URL 时才导航；若省略: 空 URL 会被错误传给 goto
                try:  # 新增代码+BrowserAutomation标签页: 捕获新标签页导航失败以便清理；若省略: goto 失败会留下空白页
                    page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)  # 修改代码+BrowserAutomation标签页: 导航新标签页到目标 URL；若省略: 新标签页不会打开指定页面
                except Exception:  # 新增代码+BrowserAutomation标签页: 导航失败时进入清理分支；若省略: 工具失败后状态会不一致
                    try:  # 新增代码+BrowserAutomation标签页: 尝试关闭失败的新页面；若省略: 新标签页可能继续占用资源
                        page.close()  # 新增代码+BrowserAutomation标签页: 关闭导航失败的新页；若省略: browser_tabs 失败但页面仍留在浏览器中
                    except Exception:  # 新增代码+BrowserAutomation标签页: 容忍页面已关闭；若省略: 关闭错误可能掩盖真正的导航错误
                        pass  # 新增代码+BrowserAutomation标签页: 保持异常分支语法完整；若省略: except 分支无语句会语法错误
                    self._forget_page(page_id)  # 新增代码+BrowserAutomation标签页: 移除失败新页映射；若省略: 列表会残留失败页面
                    raise  # 新增代码+BrowserAutomation标签页: 重新抛出导航错误；若省略: 调用方会误以为新标签打开成功
            return f"browser_tabs new 成功\npage_id={page_id}\n标题：{page.title()}\nURL：{page.url}"  # 修改代码+BrowserAutomation标签页: 返回新标签页摘要；若省略: 用户拿不到新 page_id
        if action == "switch":  # 修改代码+BrowserAutomation标签页: 处理切换当前页动作；若省略: 多标签页时无法选择操作目标
            page_id = str(arguments.get("page_id", "") or "").strip()  # 修改代码+BrowserAutomation标签页: 读取要切换的 page_id；若省略: 无法知道切到哪一页
            page_id, page = self.current_page(page_id)  # 修改代码+BrowserAutomation标签页: 复用 current_page 校验存在且未关闭；若省略: switch 可能切到已关闭页面
            self.current_page_id = page_id  # 修改代码+BrowserAutomation标签页: 设置当前页面 id；若省略: switch 动作不会影响后续工具
            return f"browser_tabs switch 成功\npage_id={page_id}\n标题：{page.title()}\nURL：{page.url}"  # 修改代码+BrowserAutomation标签页: 返回切换成功摘要；若省略: 调用方不知道当前页已切换到哪里
        if action == "close":  # 修改代码+BrowserAutomation标签页: 处理关闭标签页动作；若省略: 用户无法关闭单个页面
            page_id = str(arguments.get("page_id", "") or "").strip()  # 修改代码+BrowserAutomation标签页: 读取可选关闭 page_id；若省略: 无法支持关闭指定页面
            page_id, page = self.current_page(page_id)  # 修改代码+BrowserAutomation标签页: 缺省关闭当前页并校验页面存在；若省略: close 分支可能关闭错误对象
            try:  # 修改代码+BrowserAutomation标签页: 捕获页面关闭异常；若省略: 已关闭页面会让工具失败
                page.close()  # 修改代码+BrowserAutomation标签页: 调用 Playwright 关闭页面；若省略: 标签页仍会占用资源
            except Exception:  # 修改代码+BrowserAutomation标签页: 容忍页面已经关闭等情况；若省略: 幂等关闭体验较差
                pass  # 修改代码+BrowserAutomation标签页: 忽略关闭异常继续清理本地状态；若省略: except 分支语法不完整
            self._forget_page(page_id)  # 修改代码+BrowserAutomation标签页: 统一移除页面映射并更新当前页；若省略: 关闭逻辑会和页面 close 事件清理不一致
            return f"browser_tabs close 成功\n已关闭：{page_id}\n{self._format_tabs()}"  # 修改代码+BrowserAutomation标签页: 返回关闭结果和剩余列表；若省略: 用户不知道关闭后还剩哪些页面
        if action == "list":  # 修改代码+BrowserAutomation标签页: 仅明确 list 或默认 list 时列出标签页；若省略: 未识别动作会被静默当成 list
            return self._format_tabs()  # 修改代码+BrowserAutomation标签页: 返回当前标签页列表；若省略: list 动作没有结果
        raise RuntimeError("未知 browser_tabs action，请使用 list、switch、new 或 close。")  # 修改代码+BrowserAutomation标签页: 未识别 action 直接中文报错；若省略: 拼错动作会被静默忽略

    def browser_console(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation骨架: 声明控制台日志方法返回文本；若省略: 后续实现返回类型和协议包装不一致
        wanted_page_id = str(arguments.get("page_id", "") or "").strip()  # 新增代码+BrowserAutomation控制台: 读取可选 page_id 过滤条件；若省略: 多标签页日志无法按页面筛选
        if wanted_page_id:  # 新增代码+BrowserAutomation控制台: 只有用户传入 page_id 时才校验页面存在；若省略: 拼错 page_id 会静默返回空日志
            self.current_page(wanted_page_id)  # 新增代码+BrowserAutomation控制台: 复用页面校验逻辑确认 page_id 有效；若省略: 用户不知道是无日志还是页面 id 错
        elif self.current_page_id:  # 新增代码+BrowserAutomation控制台: 未传 page_id 且有当前页时默认筛当前页；若省略: 会把其他标签页日志混在一起
            wanted_page_id = self.current_page_id  # 新增代码+BrowserAutomation控制台: 保存当前页 id 作为默认过滤目标；若省略: 默认行为不符合 page_id 可选语义
        max_entries = safe_int(arguments.get("max_entries", 20), 20, 1, 200)  # 新增代码+BrowserAutomation控制台: 解析最多返回日志条数；若省略: 大量日志可能一次返回过多内容
        entries = [entry for entry in self.console_logs if not wanted_page_id or entry.get("page_id") == wanted_page_id]  # 新增代码+BrowserAutomation控制台: 按页面过滤 console 日志；若省略: 多页面调试信息会混杂
        entries = entries[-max_entries:]  # 新增代码+BrowserAutomation控制台: 只保留最近 max_entries 条返回；若省略: 输出可能过长且难以阅读
        if not entries:  # 新增代码+BrowserAutomation控制台: 无日志时走明确提示分支；若省略: 空字符串会让用户误以为工具失败
            return f"browser_console 无日志\npage_id={wanted_page_id or '全部'}\n最近没有捕获到 console 输出。"  # 修改代码+BrowserAutomation控制台: 明确说明没有 console 日志；若省略: 调用方无法区分空日志和工具异常
        lines = [f"browser_console 最近 {len(entries)} 条日志\npage_id={wanted_page_id or '全部'}"]  # 新增代码+BrowserAutomation控制台: 准备输出标题和过滤页；若省略: 日志列表缺少上下文
        for entry in entries:  # 新增代码+BrowserAutomation控制台: 遍历要返回的日志条目；若省略: 只能返回标题不能看到具体日志
            text, clipped = clip_text(entry.get("text", ""), 1000)  # 新增代码+BrowserAutomation控制台: 截断单条日志避免超长输出；若省略: 一条大日志可能撑爆结果
            clipped_mark = "（已截断）" if clipped else ""  # 新增代码+BrowserAutomation控制台: 标记单条日志是否被截断；若省略: 用户不知道日志是否完整
            lines.append(f"- {entry.get('time', '')} [{entry.get('page_id', '')}] {entry.get('type', '')}: {text}{clipped_mark}")  # 新增代码+BrowserAutomation控制台: 写入时间、页面、类型和文本；若省略: console 输出缺少关键定位信息
        return "\n".join(lines)  # 修改代码+BrowserAutomation控制台: 返回整理后的 console 文本；若省略: MCP client 收不到日志内容

    def browser_network(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation骨架: 声明网络日志方法返回文本；若省略: 后续实现返回类型和协议包装不一致
        wanted_page_id = str(arguments.get("page_id", "") or "").strip()  # 新增代码+BrowserAutomation网络: 读取可选 page_id 过滤条件；若省略: 多标签页网络记录无法筛选
        if wanted_page_id:  # 新增代码+BrowserAutomation网络: 只有传入 page_id 时校验页面存在；若省略: 拼错 page_id 会被误解成没有网络记录
            self.current_page(wanted_page_id)  # 新增代码+BrowserAutomation网络: 复用页面校验确认目标页可用；若省略: 错误页面 id 不会有清楚提示
        elif self.current_page_id:  # 新增代码+BrowserAutomation网络: 未传 page_id 且有当前页时默认筛当前页；若省略: 多页网络摘要可能混在一起
            wanted_page_id = self.current_page_id  # 新增代码+BrowserAutomation网络: 保存当前页 id 作为默认过滤目标；若省略: 默认 page_id 语义不稳定
        max_entries = safe_int(arguments.get("max_entries", 50), 50, 1, 400)  # 新增代码+BrowserAutomation网络: 解析最多返回网络条数；若省略: 大页面请求会输出过多记录
        entries = [entry for entry in self.network_logs if not wanted_page_id or entry.get("page_id") == wanted_page_id]  # 新增代码+BrowserAutomation网络: 按页面过滤网络摘要；若省略: 多页面请求无法区分来源
        entries = entries[-max_entries:]  # 新增代码+BrowserAutomation网络: 只返回最近 max_entries 条；若省略: 输出可能过长
        if not entries:  # 新增代码+BrowserAutomation网络: 无网络记录时走明确提示；若省略: 空输出会让用户误判工具异常
            return f"browser_network 无记录\npage_id={wanted_page_id or '全部'}\n最近没有捕获到网络请求或响应。"  # 修改代码+BrowserAutomation网络: 明确说明没有网络摘要；若省略: 调用方无法区分空记录和失败
        lines = [f"browser_network 最近 {len(entries)} 条摘要\npage_id={wanted_page_id or '全部'}\n说明：仅包含 method/url/resource_type/status，不包含请求体或敏感 header。"]  # 新增代码+BrowserAutomation网络: 准备标题并声明不含敏感数据；若省略: 用户可能误以为输出包含完整网络内容
        for entry in entries:  # 新增代码+BrowserAutomation网络: 遍历网络摘要条目；若省略: 只能看到标题看不到请求信息
            status = entry.get("status", "") if entry.get("status", "") != "" else "-"  # 新增代码+BrowserAutomation网络: 请求阶段没有状态码时显示短横线；若省略: 输出空状态不易读
            lines.append(f"- [{entry.get('page_id', '')}] {entry.get('kind', '')} {entry.get('method', '')} {status} {entry.get('resource_type', '')} {entry.get('url', '')}")  # 新增代码+BrowserAutomation网络: 输出安全网络摘要；若省略: network 工具无法展示访问过哪些 URL
        return "\n".join(lines)  # 修改代码+BrowserAutomation网络: 返回整理后的网络摘要文本；若省略: MCP client 收不到网络记录

    def browser_upload_file(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation骨架: 声明上传文件方法返回文本；若省略: 后续实现返回类型和协议包装不一致
        page_id, page = self.current_page(str(arguments.get("page_id", "") or ""))  # 修改代码+BrowserAutomation上传: 获取指定或当前页面；若省略: 上传工具不知道操作哪个标签页
        selector = str(arguments.get("selector", "") or "").strip()  # 新增代码+BrowserAutomation上传: 读取 CSS 选择器参数；若省略: 无法判断调用方是否指定文件输入框
        element_id = str(arguments.get("element_id", "") or "").strip()  # 新增代码+BrowserAutomation上传: 读取快照元素 id 参数；若省略: 无法通过快照引用定位 input
        if not selector and not element_id:  # 新增代码+BrowserAutomation上传: 要求 selector 或 element_id 至少提供一个；若省略: 上传可能误用 text/label 定位到错误元素
            raise RuntimeError("browser_upload_file 需要 selector 或 element_id 指向文件输入框。")  # 新增代码+BrowserAutomation上传: 用中文说明缺少定位信息；若省略: 用户不知道该如何选择 input
        upload_path = self.resolve_upload_path(arguments.get("path", ""))  # 新增代码+BrowserAutomation上传: 校验并解析 workspace 内上传文件；若省略: 可能上传不存在或越界文件
        locator = self.resolve_locator(page_id, page, arguments)  # 新增代码+BrowserAutomation上传: 把 selector/element_id 解析成 Playwright locator；若省略: 无法找到文件 input
        locator.set_input_files(str(upload_path))  # 新增代码+BrowserAutomation上传: 调用 Playwright 把文件放进 input[type=file]；若省略: 页面不会收到上传文件
        self._audit_browser_tool("browser_upload_file", {"page_id": page_id, "action": "upload_file", "file_present": True, "has_selector": bool(selector), "has_element_id": bool(element_id)})  # 新增代码+RealChrome审计: 上传成功后只记录文件存在和目标类型；若没有这行代码，真实 Chrome 上传动作缺少审计或可能写入文件路径/内容
        return f"browser_upload_file 成功\npage_id={page_id}\n文件：{upload_path}\nURL：{page.url}"  # 修改代码+BrowserAutomation上传: 返回上传成功和文件路径摘要；若省略: 调用方不知道上传是否完成

    def browser_downloads(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation骨架: 声明下载记录方法返回文本；若省略: 后续实现返回类型和协议包装不一致
        max_results = safe_int(arguments.get("max_results", 20), 20, 1, 100)  # 新增代码+BrowserAutomation下载: 解析最多返回下载条数；若省略: 下载记录可能一次输出过多
        entries = self.downloads[-max_results:]  # 新增代码+BrowserAutomation下载: 取最近 max_results 条下载记录；若省略: max_results 参数不会生效
        if not entries:  # 新增代码+BrowserAutomation下载: 无下载记录时走明确提示；若省略: 空列表输出会让用户误以为工具失败
            self._audit_browser_tool("browser_downloads", {"action": "downloads", "count": 0})  # 新增代码+RealChrome审计: 下载列表为空也记录安全数量摘要；若没有这行代码，真实 Chrome 下载查询无记录时没有审计留痕
            return f"browser_downloads 无记录\n目录：{self.artifacts_dir}\n最近没有捕获到下载。"  # 修改代码+BrowserAutomation下载: 返回产物目录和无记录说明；若省略: 用户不知道下载目录在哪里
        lines = [f"browser_downloads 最近 {len(entries)} 条记录\n目录：{self.artifacts_dir}"]  # 新增代码+BrowserAutomation下载: 准备下载列表标题和目录；若省略: 用户拿不到产物根目录
        for entry in entries:  # 新增代码+BrowserAutomation下载: 遍历下载记录；若省略: 只能返回标题不能列文件
            error_text = f" ERROR={entry.get('error', '')}" if entry.get("error") else ""  # 新增代码+BrowserAutomation下载: 成功记录不显示 error，失败记录显示错误详情；若省略: save_as 失败诊断不会出现在工具输出里
            lines.append(f"- {entry.get('time', '')} [{entry.get('page_id', '')}] {entry.get('filename', '')} -> {entry.get('path', '')} URL={entry.get('url', '')}{error_text}")  # 修改代码+BrowserAutomation下载: 输出文件名、路径、URL 以及失败错误；若省略 error: 下载保存失败无法被用户看见
        self._audit_browser_tool("browser_downloads", {"action": "downloads", "count": len(entries)})  # 新增代码+RealChrome审计: 下载列表有记录时只审计返回数量；若没有这行代码，真实 Chrome 下载查询缺少安全摘要审计
        return "\n".join(lines)  # 修改代码+BrowserAutomation下载: 返回整理后的下载列表；若省略: MCP client 收不到下载记录

    def browser_evaluate(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation脚本: 声明脚本执行方法返回文本；若省略: MCP 分发后无法执行 JavaScript
        script = str(arguments.get("script", "") or "").strip()  # 新增代码+BrowserAutomation脚本: 读取并清理 JavaScript 脚本文本；若省略: 空脚本或 None 会传给 Playwright 造成难懂错误
        if not script:  # 新增代码+BrowserAutomation脚本: 检查脚本不能为空；若省略: 空脚本会让 evaluate 抛出底层错误
            raise RuntimeError("browser_evaluate 缺少非空 script 参数。")  # 新增代码+BrowserAutomation脚本: 用中文说明缺少 script；若省略: 新手用户不知道该传什么
        if self.session_mode == "real_chrome":  # 新增代码+RealChrome安全: 只在真实 Chrome 模式执行敏感脚本拦截；若没有这行代码，独立 Chromium 行为会被不必要限制或真实 Chrome 缺少专门边界
            try:  # 新增代码+RealChrome安全: 捕获策略拒绝以便更新状态和写安全审计；若没有这行代码，拒绝原因无法进入 last_safety_refusal
                self.safety_policy.validate_script(script)  # 新增代码+RealChrome安全: 在取页面前拦截 cookie、storage、token、password 等敏感脚本；若没有这行代码，高风险脚本会直接接触真实登录态页面
            except RealChromeProfileError as safety_error:  # 新增代码+RealChrome安全: 捕获真实 Chrome 专用安全错误；若没有这行代码，无法转换为工具层 RuntimeError 并记录拒绝状态
                self.last_safety_refusal = str(safety_error)  # 新增代码+RealChrome安全: 保存最近拒绝原因供状态工具显示；若没有这行代码，用户看不到刚才为什么被拒绝
                try:  # 新增代码+RealChrome安全: 单独保护安全拒绝审计写入；若没有这行代码，审计失败可能掩盖真正的安全拒绝
                    self.audit_logger.record("safety_refusal", {"tool_name": "browser_evaluate", "reason": str(safety_error)})  # 新增代码+RealChrome安全: 只记录工具名和拒绝原因，不记录脚本全文；若没有这行代码，高风险拒绝缺少留痕或可能泄露脚本内容
                except Exception:  # 新增代码+RealChrome安全: 审计器异常时进入容错分支；若没有这行代码，日志写入失败会改变安全拒绝的返回结果
                    pass  # 新增代码+RealChrome安全: 忽略审计失败但继续拒绝脚本；若没有这行代码，except 分支语法不完整且可能吞掉安全错误
                raise RuntimeError(str(safety_error))  # 新增代码+RealChrome安全: 把安全策略拒绝作为工具错误返回；若没有这行代码，敏感脚本可能继续往下执行
        page_id, page = self.current_page(str(arguments.get("page_id", "") or ""))  # 修改代码+RealChrome安全: 安全检查通过后才获取指定或当前页面；若没有这行代码，脚本不知道在哪个标签页执行
        timeout_ms = safe_int(arguments.get("timeout_ms", DEFAULT_TIMEOUT_MS), DEFAULT_TIMEOUT_MS, 1, MAX_TIMEOUT_MS)  # 修改代码+BrowserAutomation脚本: 解析脚本超时并限制范围；若省略: 坏超时参数会导致默认超时不可控
        max_result_chars = safe_int(arguments.get("max_result_chars", DEFAULT_MAX_CHARS), DEFAULT_MAX_CHARS, 1, MAX_RESULT_CHARS)  # 新增代码+BrowserAutomation脚本: 解析结果最大字符数并限制范围；若省略: 大对象结果可能返回过长文本
        started_at = time.time()  # 新增代码+BrowserAutomation脚本: 记录执行开始时间用于统计耗时；若省略: 返回结果无法告诉用户脚本用了多久
        session = page.context.new_cdp_session(page)  # 修改代码+BrowserAutomation脚本: 创建 Chromium CDP 会话以使用 Runtime.evaluate 的底层 timeout；若省略: 同步死循环脚本无法被 V8/Chromium 中止
        try:  # 修改代码+BrowserAutomation脚本: 包住 CDP 执行确保 finally 能释放会话；若省略: 异常路径可能残留调试会话
            user_script_json = json.dumps(script, ensure_ascii=False)  # 修改代码+BrowserAutomation脚本: 把用户脚本安全编码成 JS 字符串字面量；若省略: 引号或换行会破坏 CDP 表达式
            expression = f"(async () => {{ const userScript = {user_script_json}; let evaluated; try {{ evaluated = eval(`(${{userScript}})`); }} catch (firstError) {{ evaluated = eval(userScript); }} const value = typeof evaluated === 'function' ? evaluated() : evaluated; return await value; }})()"  # 修改代码+BrowserAutomation脚本: 构造 async IIFE，先支持函数字符串再 fallback 到语句脚本；若省略: 函数字符串或语句形式脚本会有一类不能执行
            try:  # 修改代码+BrowserAutomation脚本: 捕获 CDP 执行层错误并转成中文 RuntimeError；若省略: 同步超时会暴露底层 Protocol error
                cdp_result = session.send("Runtime.evaluate", {"expression": expression, "awaitPromise": True, "returnByValue": True, "timeout": timeout_ms, "userGesture": True})  # 修改代码+BrowserAutomation脚本: 用 CDP Runtime.evaluate 执行并让 timeout 真正约束同步 JS；若省略: while(true) 会占住事件循环
            except Exception as cdp_error:  # 修改代码+BrowserAutomation脚本: 捕获 Runtime.evaluate 直接抛出的超时或协议错误；若省略: MCP 返回信息不够中文友好
                raise RuntimeError(f"browser_evaluate 执行 JavaScript 失败：{cdp_error}")  # 修改代码+BrowserAutomation脚本: 把 CDP 执行失败包装成中文错误；若省略: 用户难以理解底层协议异常
            exception_details = cdp_result.get("exceptionDetails")  # 修改代码+BrowserAutomation脚本: 读取 CDP 返回的异常详情；若省略: 脚本异常会被当成普通结果
            if exception_details:  # 修改代码+BrowserAutomation脚本: 发现 JS 异常时转成中文 RuntimeError；若省略: 调用方看不到清晰失败原因
                exception_text = str(exception_details.get("text", "") or exception_details.get("exception", {}).get("description", "") or exception_details)  # 修改代码+BrowserAutomation脚本: 提取异常摘要文本；若省略: 错误信息可能为空或难以理解
                raise RuntimeError(f"browser_evaluate 执行 JavaScript 失败：{exception_text}")  # 修改代码+BrowserAutomation脚本: 抛出中文脚本执行错误；若省略: JS 报错不会按 MCP 错误返回
            remote_result = cdp_result.get("result", {})  # 修改代码+BrowserAutomation脚本: 读取 CDP Runtime.evaluate 的结果对象；若省略: 无法提取脚本返回值
            if "value" in remote_result:  # 修改代码+BrowserAutomation脚本: 优先读取 returnByValue 的普通 JSON 值；若省略: 字符串、数字和对象结果无法返回
                result = remote_result.get("value")  # 修改代码+BrowserAutomation脚本: 保存普通可序列化返回值；若省略: evaluate 会丢失主要结果
            elif "unserializableValue" in remote_result:  # 修改代码+BrowserAutomation脚本: 处理 NaN、Infinity、-0 等不可 JSON 序列化值；若省略: 特殊数字返回会变成空
                result = remote_result.get("unserializableValue")  # 修改代码+BrowserAutomation脚本: 保存不可序列化值的字符串表示；若省略: 用户看不到特殊 JS 数值
            else:  # 修改代码+BrowserAutomation脚本: 普通值和特殊值都没有时使用描述兜底；若省略: undefined 或函数等结果可能无文本
                result = remote_result.get("description", "")  # 修改代码+BrowserAutomation脚本: 保存 CDP description 作为兜底输出；若省略: 某些返回类型会显示为空
        finally:  # 修改代码+BrowserAutomation脚本: 不论成功失败都断开 CDP 会话；若省略: 长会话可能积累调试连接
            session.detach()  # 修改代码+BrowserAutomation脚本: 释放本次 CDP session；若省略: 后续调试和资源清理可能受影响
        elapsed_ms = int((time.time() - started_at) * 1000)  # 新增代码+BrowserAutomation脚本: 把耗时换算成毫秒整数；若省略: 用户无法判断脚本执行慢不慢
        result_text, result_clipped = clip_text(result, max_result_chars)  # 新增代码+BrowserAutomation脚本: 把结果转成文本并按上限截断；若省略: 非字符串结果或超长结果会难以返回
        clipped_text = "已截断" if result_clipped else "未截断"  # 新增代码+BrowserAutomation脚本: 标注结果是否被截断；若省略: 用户不知道结果是不是完整的
        self._audit_browser_tool("browser_evaluate", {"page_id": page_id, "script_allowed": True})  # 新增代码+RealChrome审计: evaluate 成功后只记录允许标记和 page_id；若没有这行代码，真实 Chrome 脚本执行缺少审计或可能误写脚本全文
        return f"browser_evaluate 成功\npage_id={page_id}\n标题：{page.title()}\nURL：{page.url}\n耗时毫秒：{elapsed_ms}\n结果截断：{clipped_text}\n结果文本：{result_text}"  # 修改代码+BrowserAutomation脚本: 返回脚本执行摘要和结果文本；若省略: 调用方拿不到 evaluate 的输出

    def browser_close(self, arguments: dict[str, Any]) -> str:  # 修改代码+BrowserAutomation骨架: 声明关闭方法返回文本；若省略: 后续实现返回类型和协议包装不一致
        if bool(arguments.get("all", False)):  # 修改代码+BrowserAutomation关闭: all 为真时关闭整个会话；若省略: 用户无法一次释放所有浏览器资源
            self.close_all()  # 修改代码+BrowserAutomation关闭: 调用统一清理方法；若省略: context/browser/playwright 可能残留
            return "browser_close 成功：已关闭整个浏览器会话"  # 修改代码+BrowserAutomation关闭: 返回整会话关闭成功文本；若省略: 调用方不知道资源已释放
        return self.browser_tabs({"action": "close", "page_id": str(arguments.get("page_id", "") or "")})  # 修改代码+BrowserAutomation关闭: 复用标签页关闭逻辑关闭单页；若省略: 单页关闭会和 tabs close 行为不一致

    def close_all(self) -> None:  # 新增代码+BrowserAutomation清理: 定义安全清理方法；若省略: server 退出时可能残留浏览器进程
        if self.session_mode == "real_chrome":  # 修改代码+RealChrome关闭: 真实 Chrome 模式走安全断开分支；若省略: close_all 会误关用户真实 Chrome
            self._disconnect_real_chrome_session(False)  # 修改代码+RealChrome关闭: 复用断开工具的安全逻辑且默认不关闭 Chrome；若没有这行代码，close_all 和断开工具可能出现两套行为
            self.console_logs.clear()  # 修改代码+RealChrome关闭: 清空控制台日志；若没有这行代码，新会话可能看到真实 Chrome 旧日志
            self.network_logs.clear()  # 修改代码+RealChrome关闭: 清空网络日志；若没有这行代码，新会话可能看到真实 Chrome 旧请求
            self.downloads.clear()  # 修改代码+RealChrome关闭: 清空下载记录；若没有这行代码，新会话可能看到旧下载记录
            return  # 修改代码+RealChrome关闭: 真实 Chrome 分支到此结束，绝不继续 context.close/browser.close；若省略: 仍会落入误关真实 Chrome 的旧清理逻辑
        for page in list(self.pages.values()):  # 修改代码+BrowserAutomation清理: 先逐个关闭已登记页面；若省略: 页面事件和资源可能残留到上下文关闭阶段
            try:  # 修改代码+BrowserAutomation清理: 捕获单页关闭异常；若省略: 一个已关闭页面会中断全部清理
                page.close()  # 修改代码+BrowserAutomation清理: 关闭 Playwright 页面；若省略: 标签页资源不能主动释放
            except Exception:  # 修改代码+BrowserAutomation清理: 容忍页面已经关闭或浏览器已退出；若省略: 清理不是幂等的
                pass  # 修改代码+BrowserAutomation清理: 忽略单页关闭错误继续清理；若省略: except 分支语法不完整
        self.pages.clear()  # 修改代码+BrowserAutomation清理: 清空页面映射；若省略: 已关闭页面引用会残留
        self.next_page_index = 1  # 修改代码+BrowserAutomation清理: 整个浏览器会话关闭后重置页面编号，因为页面集合已清空且不会覆盖旧页面；若省略: 新会话页面编号会继续增长不利于新手理解
        self.element_refs.clear()  # 修改代码+BrowserAutomation清理: 清空元素引用；若省略: 新会话可能拿到旧元素数据
        self.current_page_id = None  # 修改代码+BrowserAutomation清理: 清空当前页 id；若省略: 后续可能指向不存在页面
        if self.context is not None:  # 修改代码+BrowserAutomation清理: 只在上下文存在时关闭；若省略: None 会触发属性错误
            try:  # 修改代码+BrowserAutomation清理: 捕获上下文关闭异常；若省略: 已关闭上下文会中断清理
                self.context.close()  # 修改代码+BrowserAutomation清理: 关闭浏览器上下文；若省略: cookies、页面和下载上下文可能残留
            except Exception:  # 修改代码+BrowserAutomation清理: 容忍上下文已关闭；若省略: 二次关闭会影响退出
                pass  # 修改代码+BrowserAutomation清理: 忽略上下文关闭错误；若省略: except 分支语法不完整
        self.context = None  # 修改代码+BrowserAutomation清理: 清空上下文属性；若省略: 后续可能误用已关闭对象
        if self.browser is not None:  # 修改代码+BrowserAutomation清理: 只在浏览器存在时关闭；若省略: None 会触发属性错误
            try:  # 修改代码+BrowserAutomation清理: 捕获浏览器关闭异常；若省略: 已关闭浏览器会中断清理
                self.browser.close()  # 修改代码+BrowserAutomation清理: 关闭 Chromium；若省略: 浏览器进程可能残留
            except Exception:  # 修改代码+BrowserAutomation清理: 容忍浏览器已关闭；若省略: 二次关闭可能报错
                pass  # 修改代码+BrowserAutomation清理: 忽略浏览器关闭错误；若省略: except 分支语法不完整
        self.browser = None  # 修改代码+BrowserAutomation清理: 清空浏览器属性；若省略: 后续可能误认为浏览器仍可复用
        if self.playwright is not None:  # 新增代码+BrowserAutomation清理: 只在 Playwright 存在时 stop；若省略: None 会触发属性错误
            try:  # 新增代码+BrowserAutomation清理: 捕获 stop 异常；若省略: Playwright 已停止时可能报错
                self.playwright.stop()  # 新增代码+BrowserAutomation清理: 停止 Playwright 驱动；若省略: 驱动进程可能残留
            except Exception:  # 新增代码+BrowserAutomation清理: 忽略 stop 异常；若省略: 清理阶段会影响主流程退出
                pass  # 新增代码+BrowserAutomation清理: 保持清理尽力而为；若省略: except 分支语法不完整
        self.playwright = None  # 新增代码+BrowserAutomation清理: 清空 Playwright 状态；若省略: 后续可能误认为仍可用
        self.console_logs.clear()  # 修改代码+BrowserAutomation清理: 清空控制台日志；若省略: 新会话可能看到旧日志
        self.network_logs.clear()  # 修改代码+BrowserAutomation清理: 清空网络日志；若省略: 新会话可能看到旧请求
        self.downloads.clear()  # 修改代码+BrowserAutomation清理: 清空下载记录；若省略: 新会话可能看到旧下载


SERVER: BrowserAutomationServer | None = None  # 新增代码+BrowserAutomation全局: 保存可复用 server 实例；若省略: 每次 tools/call 都无法共享浏览器状态


def handle_tools_call(params: dict[str, Any]) -> dict[str, Any]:  # 新增代码+BrowserAutomation协议: 处理 MCP tools/call 请求；若省略: 已列出的工具无法被调用
    global SERVER  # 新增代码+BrowserAutomation协议: 声明会创建或复用全局 SERVER；若省略: Python 会把 SERVER 当成本地变量导致错误
    name = str(params.get("name", "")).strip()  # 新增代码+BrowserAutomation协议: 读取工具名；若省略: 无法知道 client 要调用哪个工具
    arguments = params.get("arguments", {})  # 新增代码+BrowserAutomation协议: 读取工具参数；若省略: 工具拿不到输入
    if not isinstance(arguments, dict):  # 新增代码+BrowserAutomation协议: 确保参数是对象；若省略: 工具方法里调用 get 可能崩溃
        arguments = {}  # 新增代码+BrowserAutomation协议: 非对象参数兜底为空字典；若省略: 坏参数会让 server 不稳定
    if SERVER is None:  # 新增代码+BrowserAutomation协议: 首次调用时创建 server；若省略: SERVER 为空时无法调用方法
        SERVER = BrowserAutomationServer(WORKSPACE)  # 新增代码+BrowserAutomation协议: 用当前工作区初始化 server；若省略: 工具没有状态容器
    return tool_result(SERVER.call(name, arguments))  # 修改代码+BrowserAutomation协议: 把工具文本结果包装成 MCP content；若省略: JSON-RPC result 不符合 MCP tools/call 格式


def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:  # 新增代码+BrowserAutomation协议: 处理单条 JSON-RPC 消息；若省略: 主循环无法响应 MCP 请求
    method = str(message.get("method", ""))  # 新增代码+BrowserAutomation协议: 提取请求方法；若省略: 无法区分 initialize、tools/list 和 tools/call
    request_id = message.get("id")  # 新增代码+BrowserAutomation协议: 保存请求 id；若省略: 响应无法与请求匹配
    params = message.get("params", {})  # 新增代码+BrowserAutomation协议: 提取请求参数；若省略: tools/call 拿不到工具名和参数
    if request_id is None and method.startswith("notifications/"):  # 修改代码+BrowserAutomation协议: 无 id 的 notifications 都是通知应静默忽略；若省略: 未知通知会被错误地返回 error
        return None  # 修改代码+BrowserAutomation协议: notification 不返回响应；若省略: MCP client 可能收到不该有的错误包
    if method == "notifications/initialized":  # 新增代码+BrowserAutomation协议: 识别初始化完成通知；若省略: notification 会收到不该有的错误响应
        return None  # 新增代码+BrowserAutomation协议: notification 不返回响应；若省略: MCP 初始化流程可能不符合预期
    if method == "initialize":  # 新增代码+BrowserAutomation协议: 处理 MCP 初始化握手；若省略: client.start 会失败
        return make_response(request_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "browser_automation", "version": "0.1"}})  # 新增代码+BrowserAutomation协议: 返回 server 名称、版本和 tools 能力；若省略: client 不知道本 server 支持工具
    if method == "tools/list":  # 新增代码+BrowserAutomation协议: 处理工具列表请求；若省略: agent 看不到 14 个浏览器工具
        return make_response(request_id, {"tools": TOOLS})  # 新增代码+BrowserAutomation协议: 返回完整工具清单；若省略: tools/list 测试无法通过
    if method == "tools/call":  # 新增代码+BrowserAutomation协议: 处理工具调用请求；若省略: 工具只能列出不能调用
        if not isinstance(params, dict):  # 新增代码+BrowserAutomation协议: 确保 params 是对象；若省略: 坏请求可能触发属性错误
            return make_error(request_id, -32602, "tools/call params 必须是对象。")  # 新增代码+BrowserAutomation协议: 返回清楚的参数错误；若省略: 用户看不到具体原因
        try:  # 新增代码+BrowserAutomation协议: 捕获工具运行异常并转成 JSON-RPC error；若省略: 一个未实现工具会杀死 server
            return make_response(request_id, handle_tools_call(params))  # 新增代码+BrowserAutomation协议: 调用工具并包装成功响应；若省略: 成功结果无法返回 client
        except Exception as error:  # 新增代码+BrowserAutomation协议: 捕获工具异常；若省略: 未实现提示会变成进程崩溃
            return make_error(request_id, -32000, str(error))  # 新增代码+BrowserAutomation协议: 把异常转成可读 MCP 错误；若省略: agent 难以解释失败原因
    return make_error(request_id, -32601, f"未知 MCP 方法：{method}")  # 新增代码+BrowserAutomation协议: 未知方法返回标准错误；若省略: 协议问题难以排查


def write_message(message: dict[str, Any]) -> None:  # 新增代码+BrowserAutomation协议: 向 stdout 写出响应；若省略: 主循环需要重复序列化逻辑
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")  # 新增代码+BrowserAutomation协议: 写出单行 JSON 并保留中文；若省略: client 的 readline 读不到完整响应
    sys.stdout.flush()  # 新增代码+BrowserAutomation协议: 立即刷新输出；若省略: 响应可能卡在缓冲区导致超时


def run_server() -> None:  # 新增代码+BrowserAutomation协议: 运行 stdio MCP server 主循环；若省略: 脚本启动后不会处理请求
    try:  # 新增代码+BrowserAutomation协议: 确保退出时执行清理；若省略: 异常或 EOF 后可能残留状态
        for raw_line in sys.stdin:  # 新增代码+BrowserAutomation协议: 逐行读取 JSON-RPC 请求；若省略: server 收不到 client 消息
            raw_line = raw_line.strip()  # 新增代码+BrowserAutomation协议: 去掉换行和边缘空白；若省略: 空白输入处理不整洁
            if not raw_line:  # 新增代码+BrowserAutomation协议: 跳过空行；若省略: 空行会触发 JSON 解析错误
                continue  # 新增代码+BrowserAutomation协议: 继续等待下一条消息；若省略: 空行会进入解析流程
            try:  # 新增代码+BrowserAutomation协议: 捕获单条消息的解析和处理错误；若省略: 坏消息会让 server 退出
                message = json.loads(raw_line)  # 新增代码+BrowserAutomation协议: 解析 JSON-RPC 文本；若省略: server 无法理解请求内容
                response = handle_message(message if isinstance(message, dict) else {})  # 新增代码+BrowserAutomation协议: 只把对象消息交给处理器；若省略: 非对象 JSON 可能触发属性错误
            except Exception as error:  # 新增代码+BrowserAutomation协议: 捕获解析或处理异常；若省略: 坏输入会导致进程崩溃
                response = make_error(None, -32700, f"JSON-RPC 消息处理失败：{error}")  # 新增代码+BrowserAutomation协议: 返回可读解析错误；若省略: client 只会看到连接断开
            if response is not None:  # 新增代码+BrowserAutomation协议: 仅普通请求需要响应；若省略: notification 会被写成无效响应
                write_message(response)  # 新增代码+BrowserAutomation协议: 把响应写回 client；若省略: client 会一直等待
    finally:  # 新增代码+BrowserAutomation清理: 主循环结束时进入清理；若省略: EOF 或异常后资源可能不释放
        if SERVER is not None:  # 新增代码+BrowserAutomation清理: 只在 server 已创建时清理；若省略: 未调用工具时会访问 None
            SERVER.close_all()  # 新增代码+BrowserAutomation清理: 尽力关闭浏览器相关状态；若省略: 后续真实实现可能残留 Chromium


if __name__ == "__main__":  # 新增代码+BrowserAutomation入口: 仅脚本直接运行时启动 MCP server；若省略: 被测试导入时也可能阻塞 stdin
    run_server()  # 新增代码+BrowserAutomation入口: 启动 stdio 主循环；若省略: MCP 配置启动脚本后会立即退出
