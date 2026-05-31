"""Real Chrome profile automation helpers for safe local CDP startup."""  # 新增代码+RealChrome: 说明本模块负责真实 Chrome profile 自动化辅助；若省略: 读代码的人很难快速知道这个文件的用途
from __future__ import annotations  # 新增代码+RealChrome: 允许类型标注更稳定地向前兼容；若省略: 某些较新的类型写法在旧解释阶段可能更容易出问题

import json  # 新增代码+RealChrome: 用来解析 CDP /json/version 和写审计 JSONL；若省略: 无法确认调试端点返回的是合法 JSON
import os  # 新增代码+RealChrome: 用来读取 Windows 常见目录环境变量；若省略: 默认路径只能写死，跨机器更容易失败
import re  # 新增代码+RealChrome: 用来识别 Function 构造器的空白和动态属性变体；若省略: Function ("...") 或 ["Function"] 这类危险入口会漏拦
import socket  # 新增代码+RealChrome: 用来检测 127.0.0.1 端口是否可绑定；若省略: 无法安全避开已占用调试端口
import subprocess  # 新增代码+RealChrome: 用来调用 tasklist 检测 chrome.exe 是否运行；若省略: 无法发现 profile 可能被 Chrome 锁住
import time  # 新增代码+RealChrome: 用来控制 CDP 端点轮询超时时间；若省略: 等待调试端点时无法准确停止
import urllib.error  # 新增代码+RealChrome: 用来捕获 urllib 请求失败；若省略: CDP 未启动时异常会直接冲出函数
import urllib.request  # 新增代码+RealChrome: 用来请求本机 CDP /json/version；若省略: 无法判断 Chrome 调试端点是否已经可用
from dataclasses import dataclass  # 新增代码+RealChrome: 用来定义不可变配置和诊断结果；若省略: 公开 API 会缺少测试要求的数据结构
from pathlib import Path  # 新增代码+RealChrome: 用来跨平台拼接和比较文件路径；若省略: 路径逻辑会退回易错字符串拼接
from typing import Any  # 新增代码+RealChrome: 用来标注审计 details 的任意值；若省略: 类型提示无法表达 JSON 风格输入


class RealChromeProfileError(RuntimeError):  # 新增代码+RealChrome: 定义真实 Chrome profile 专用错误；若省略: 调用方无法区分安全拒绝和普通运行错误
    """Raised when real Chrome profile automation would be unsafe."""  # 新增代码+RealChrome: 说明这个异常代表安全边界被触发；若省略: 读错误类时不知道什么时候会抛出


@dataclass(frozen=True)  # 新增代码+RealChrome: 让配置对象不可变，避免启动过程中被意外改掉；若省略: 后续代码可能悄悄改配置导致排查困难
class ChromeProfileConfig:  # 新增代码+RealChrome: 保存启动真实 Chrome profile 所需配置；若省略: 公开 API 缺少统一配置载体
    chrome_path: Path  # 新增代码+RealChrome: 保存 chrome.exe 路径；若省略: 启动命令不知道要运行哪个浏览器
    user_data_dir: Path  # 新增代码+RealChrome: 保存 Chrome User Data 根目录；若省略: 无法复用用户指定的真实 profile
    profile_directory: str  # 新增代码+RealChrome: 保存 profile 子目录名称；若省略: 可能启动到错误的 Chrome 身份
    debug_port: int  # 新增代码+RealChrome: 保存 CDP 调试端口；若省略: 后续连接 Chrome 时不知道访问哪个端口


@dataclass(frozen=True)  # 新增代码+RealChrome: 让诊断结果固定，避免报告生成后被误改；若省略: 调用方看到的状态可能前后不一致
class ChromeProfileDiagnostic:  # 新增代码+RealChrome: 描述真实 Chrome 环境是否可用；若省略: 公开诊断 API 没有结构化返回值
    status: str  # 新增代码+RealChrome: 保存 available/needs_user_action/blocked 状态；若省略: 调用方无法快速判断下一步动作
    chrome_path: str  # 新增代码+RealChrome: 保存检测到的 Chrome 路径文本；若省略: 用户不知道 helper 找到了哪个浏览器
    user_data_dir: str  # 新增代码+RealChrome: 保存检测到的 User Data 路径文本；若省略: 用户不知道 profile 根目录是否正确
    chrome_running: bool  # 新增代码+RealChrome: 记录 Chrome 是否正在运行；若省略: 用户不知道是否需要先关闭 Chrome
    port_available: bool  # 新增代码+RealChrome: 记录默认调试端口是否可用；若省略: 用户不知道端口冲突风险
    messages: list[str]  # 新增代码+RealChrome: 保存给用户看的诊断提示；若省略: 状态原因只能靠猜


def _path_exists_via_powershell(path: Path) -> bool:  # 修改代码+RealChromePathFallback: Python 被 Windows 拒绝读取路径时，用 PowerShell 只读确认路径是否存在；若没有这行代码，真实 Chrome User Data 会被误判为不存在
    escaped_path = str(path).replace("'", "''")  # 修改代码+RealChromePathFallback: 转义 PowerShell 单引号字符串里的路径；若没有这行代码，路径包含单引号时会破坏 Test-Path 命令
    script = f"if (Test-Path -LiteralPath '{escaped_path}') {{ 'true' }}"  # 修改代码+RealChromePathFallback: 把带空格路径安全放进 PowerShell 命令；若没有这行代码，User Data 里的空格会让 fallback 检测失败
    command = ["powershell", "-NoProfile", "-Command", script]  # 修改代码+RealChromePathFallback: 以参数列表执行 PowerShell，避免外层 shell 再解释；若没有这行代码，路径存在性 fallback 无法运行
    try:  # 修改代码+RealChromePathFallback: 捕获 PowerShell 不可用、超时或系统拒绝；若没有这行代码，fallback 本身失败会让 mcp-doctor 崩溃
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)  # 修改代码+RealChromePathFallback: 执行 Test-Path 并读取文本输出；若没有这行代码，无法得到第二种存在性证据
    except (OSError, subprocess.SubprocessError):  # 修改代码+RealChromePathFallback: 把命令执行异常转换成 False；若没有这行代码，权限兼容分支会抛出低层异常
        return False  # 修改代码+RealChromePathFallback: fallback 不可用时保守认为没有确认存在；若没有这行代码，调用方无法继续检查其它候选路径
    if completed.returncode != 0:  # 修改代码+RealChromePathFallback: PowerShell 非零退出说明本次确认失败；若没有这行代码，错误输出可能被误当成功
        return False  # 修改代码+RealChromePathFallback: 确认失败时不返回候选路径；若没有这行代码，可能把未确认路径交给 Chrome 启动
    return "true" in completed.stdout.lower()  # 修改代码+RealChromePathFallback: 只有 Test-Path 明确输出 true 才承认路径存在；若没有这行代码，空输出会被误当成功


def _existing_path(paths: list[Path]) -> Path | None:  # 新增代码+RealChrome: 在候选路径中找第一个存在的路径；若省略: Chrome 和 profile 查找逻辑会重复散落
    for path in paths:  # 新增代码+RealChrome: 逐个检查候选路径；若省略: 函数无法遍历所有可能安装位置
        try:  # 修改代码+RealChrome: 检查候选路径时吸收 Windows 权限异常；若没有这行代码，mcp-doctor 会因为无权读取真实 Chrome profile 目录而直接崩溃
            path_exists = path.exists()  # 修改代码+RealChrome: 把 exists 结果先保存到变量；若没有这行代码，后续无法区分存在、缺失和权限失败后的跳过逻辑
        except OSError:  # 修改代码+RealChrome: 捕获 PermissionError 等系统路径访问异常；若没有这行代码，不可访问目录会中断整个诊断流程
            if _path_exists_via_powershell(path):  # 修改代码+RealChromePathFallback: Python 权限拒绝时改用 PowerShell Test-Path 补证；若没有这行代码，可见终端验收会把真实 User Data 目录误判为缺失
                return path  # 修改代码+RealChromePathFallback: fallback 明确确认存在就返回候选路径；若没有这行代码，已确认存在的 Chrome profile 仍会被丢弃
            continue  # 修改代码+RealChrome: 跳过不可访问候选路径继续检查其它候选；若没有这行代码，一个坏候选会让后续候选也没有机会被检测
        if path_exists:  # 修改代码+RealChrome: 只接受真实存在且可访问检查成功的路径；若省略: 可能返回不存在的 chrome.exe 导致启动失败
            return path  # 新增代码+RealChrome: 找到第一个可用路径就返回；若省略: 即使找到也会继续走到 None
    return None  # 新增代码+RealChrome: 没有任何候选存在时返回空值；若省略: 调用方无法区分没找到和异常


def _is_loopback_port_available(port: int) -> bool:  # 新增代码+RealChrome: 检查指定本机端口是否可绑定；若省略: 无法知道首选调试端口是否已被占用
    if port < 1 or port > 65535:  # 新增代码+RealChrome: 拒绝 TCP 合法范围外的端口；若省略: socket.bind 可能抛出不直观错误
        return False  # 新增代码+RealChrome: 非法端口直接视为不可用；若省略: 调用方可能把 0 或超大端口当成可用
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:  # 新增代码+RealChrome: 创建临时 IPv4 TCP socket；若省略: 无法实际验证端口绑定能力
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 新增代码+RealChrome: 减少刚释放端口造成的测试抖动；若省略: 端口可用判断可能受短暂 TIME_WAIT 影响
        try:  # 新增代码+RealChrome: 捕获端口占用或权限异常；若省略: 一个占用端口会让诊断流程崩溃
            sock.bind(("127.0.0.1", port))  # 新增代码+RealChrome: 只在本机回环地址上尝试绑定；若省略: 可能错误检测到外部网卡行为
        except OSError:  # 新增代码+RealChrome: 处理端口不可绑定的系统错误；若省略: 端口冲突不会被转换成 False
            return False  # 新增代码+RealChrome: 绑定失败说明端口当前不可用；若省略: 调用方可能继续使用冲突端口
    return True  # 新增代码+RealChrome: 临时绑定成功说明端口可用；若省略: 可用端口也会被误判为不可用


_SENSITIVE_KEY_FRAGMENTS = (  # 修改代码+RealChrome: 改为敏感片段匹配而不是精确 key 匹配；若省略: access_token、secretKey 这类变体会漏写进日志
    "authorization",  # 修改代码+RealChrome: 匹配 authorization 和 AuthorizationHeader；若省略: 鉴权头变体可能泄露到日志
    "cookie",  # 修改代码+RealChrome: 匹配 cookie 和 set-cookie 等字段；若省略: 登录态字段可能泄露到日志
    "localstorage",  # 修改代码+RealChrome: 匹配 localStorageData 等字段；若省略: 浏览器本地存储可能泄露到日志
    "sessionstorage",  # 修改代码+RealChrome: 匹配 sessionStorageData 等字段；若省略: 当前会话数据可能泄露到日志
    "password",  # 修改代码+RealChrome: 匹配 password 字段；若省略: 密码相关字段可能泄露到日志
    "token",  # 修改代码+RealChrome: 匹配 access_token、refresh_token 和 authToken；若省略: token 变体可能泄露到日志
    "secret",  # 修改代码+RealChrome: 匹配 secret 和 secretKey；若省略: 密钥类字段可能泄露到日志
    "apikey",  # 修改代码+RealChrome: 匹配 api_key 和 apiKey；若省略: API key 字段可能泄露到日志
    "bearer",  # 修改代码+RealChrome: 匹配 bearer 凭据字段；若省略: Bearer token 可能泄露到日志
    "requestbody",  # 修改代码+RealChrome: 匹配 request_body 和 requestBody；若省略: 请求正文可能泄露到日志
    "responsebody",  # 修改代码+RealChrome: 匹配 response_body 和 responseBody；若省略: 响应正文可能泄露到日志
)  # 修改代码+RealChrome: 结束敏感片段元组；若省略: Python 元组语法不完整


def _normalize_sensitive_text(text: str) -> str:  # 新增代码+RealChrome: 把 key 或脚本文本规范化为只含字母数字的小写串；若省略: 引号、下划线、点号等混淆写法会绕过敏感检测
    return "".join(character.lower() for character in text if character.isalnum())  # 新增代码+RealChrome: 去掉非字母数字并小写；若省略: access_token、document["cookie"] 等变体无法统一识别


def _is_sensitive_key(key: object) -> bool:  # 新增代码+RealChrome: 判断审计字段名是否包含敏感片段；若省略: _redact_details 仍只能做脆弱的精确匹配
    normalized_key = _normalize_sensitive_text(str(key))  # 新增代码+RealChrome: 规范化字段名再比较；若省略: api_key、authToken 这类格式变化会漏掉
    return any(fragment in normalized_key for fragment in _SENSITIVE_KEY_FRAGMENTS)  # 新增代码+RealChrome: 只要包含任一敏感片段就打码；若省略: 常见敏感字段变体不会被覆盖


def _cdp_version_payload_is_trusted(payload: Any, port: int) -> bool:  # 新增代码+RealChrome: 判断 /json/version 是否像可信本机 Chrome/CDP 响应；若省略: 任意本地 JSON 服务可能被误认为 Chrome
    if not isinstance(payload, dict):  # 新增代码+RealChrome: 只接受 JSON 对象；若省略: JSON 数组或字符串也可能误过校验
        return False  # 新增代码+RealChrome: 非对象响应不是 Chrome/CDP 版本信息；若省略: 调用方可能连接到错误服务
    web_socket_debugger_url = payload.get("webSocketDebuggerUrl")  # 新增代码+RealChrome: 读取 CDP websocket 地址；若省略: 无法确认调试连接是否指向本机指定端口
    if isinstance(web_socket_debugger_url, str):  # 新增代码+RealChrome: 只有字符串 websocket 地址才可继续校验；若省略: 非字符串字段可能被误当可信
        allowed_prefixes = (f"ws://127.0.0.1:{port}/", f"ws://localhost:{port}/")  # 新增代码+RealChrome: 只信任本机回环和当前端口；若省略: 恶意或错误主机的 websocket 可能被接受
        return web_socket_debugger_url.startswith(allowed_prefixes)  # 新增代码+RealChrome: websocket 必须指向 127.0.0.1 或 localhost 的同一端口；若省略: 远端 websocket 可能被误连
    browser_name = payload.get("Browser")  # 新增代码+RealChrome: 读取 Chrome/CDP 常见 Browser 字段；若省略: 无 websocket 的版本响应无法被安全识别
    if isinstance(browser_name, str):  # 新增代码+RealChrome: 只接受字符串 Browser 字段；若省略: 非字符串字段可能被误当可信
        return "Chrome" in browser_name or "Chromium" in browser_name  # 新增代码+RealChrome: Browser 必须明确包含 Chrome 或 Chromium；若省略: 任意带 Browser key 的 JSON 都会成功
    return False  # 新增代码+RealChrome: Protocol-Version 只能辅助，不能单独证明是 Chrome/CDP；若省略: 任意协议版本字段可能误过校验


def _redact_details(value: Any) -> Any:  # 新增代码+RealChrome: 递归清理审计详情中的敏感字段；若省略: 嵌套 dict/list 里的敏感数据会漏掉
    if isinstance(value, dict):  # 新增代码+RealChrome: 针对字典按 key 做敏感字段判断；若省略: 最常见的结构化日志无法过滤
        redacted: dict[str, Any] = {}  # 新增代码+RealChrome: 准备保存清理后的字典；若省略: 无处放过滤结果
        for key, item in value.items():  # 新增代码+RealChrome: 遍历每个字段；若省略: 无法逐项判断是否敏感
            if _is_sensitive_key(key):  # 修改代码+RealChrome: 使用规范化片段匹配识别敏感 key；若省略: access_token、AuthorizationHeader 等变体会原样写入日志
                redacted[str(key)] = "[REDACTED]"  # 新增代码+RealChrome: 用固定文本替代敏感值；若省略: 日志读者看不出字段被安全处理
            else:  # 新增代码+RealChrome: 非敏感 key 继续递归处理；若省略: 安全字段会被错误丢弃
                redacted[str(key)] = _redact_details(item)  # 新增代码+RealChrome: 保留非敏感字段并清理其子结构；若省略: 嵌套敏感字段可能漏掉
        return redacted  # 新增代码+RealChrome: 返回清理后的字典；若省略: 调用方拿不到处理结果
    if isinstance(value, list):  # 新增代码+RealChrome: 针对列表逐项清理；若省略: details 中的列表数据无法递归过滤
        return [_redact_details(item) for item in value]  # 新增代码+RealChrome: 返回清理后的列表；若省略: 列表中的敏感 dict 可能原样保存
    return value  # 新增代码+RealChrome: 普通值直接保留；若省略: 数字、布尔值和普通字符串会被意外变空


class ChromeProfileManager:  # 新增代码+RealChrome: 负责发现 Windows Chrome 路径和运行状态；若省略: 上层没有统一入口做环境探测
    def __init__(self, program_files: Path | None = None, program_files_x86: Path | None = None, local_app_data: Path | None = None) -> None:  # 新增代码+RealChrome: 允许测试注入路径，也允许生产读取环境变量；若省略: 测试会依赖真实机器目录
        self.program_files = program_files or Path(os.environ.get("ProgramFiles", r"C:\Program Files"))  # 新增代码+RealChrome: 保存 64 位 Program Files 路径；若省略: 无法查找常见 64 位 Chrome 安装
        self.program_files_x86 = program_files_x86 or Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))  # 新增代码+RealChrome: 保存 32 位 Program Files 路径；若省略: 无法查找旧版或 32 位 Chrome 安装
        self.local_app_data = local_app_data or Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))  # 新增代码+RealChrome: 保存用户本地应用数据路径；若省略: 无法查找用户级 Chrome 和 profile 数据

    def chrome_path_candidates(self) -> list[Path]:  # 新增代码+RealChrome: 返回 chrome.exe 的候选路径列表；若省略: 测试和诊断无法检查候选生成
        return [  # 新增代码+RealChrome: 用稳定顺序返回最常见安装位置；若省略: 调用方拿不到任何候选路径
            self.program_files / "Google" / "Chrome" / "Application" / "chrome.exe",  # 新增代码+RealChrome: 添加 64 位系统安装路径；若省略: 大多数 Windows 安装可能找不到 Chrome
            self.program_files_x86 / "Google" / "Chrome" / "Application" / "chrome.exe",  # 新增代码+RealChrome: 添加 32 位系统安装路径；若省略: 旧环境可能找不到 Chrome
            self.local_app_data / "Google" / "Chrome" / "Application" / "chrome.exe",  # 新增代码+RealChrome: 添加用户级安装路径；若省略: 仅当前用户安装的 Chrome 会被漏掉
        ]  # 新增代码+RealChrome: 结束候选列表；若省略: Python 列表语法不完整

    def user_data_dir_candidates(self) -> list[Path]:  # 新增代码+RealChrome: 返回 Chrome User Data 候选目录；若省略: 诊断无法找到真实 profile 根目录
        return [  # 新增代码+RealChrome: 用列表承载将来可能扩展的 profile 根目录；若省略: 调用方拿不到候选集合
            self.local_app_data / "Google" / "Chrome" / "User Data",  # 新增代码+RealChrome: 添加 Windows 默认 User Data 路径；若省略: 真实 Chrome profile 根目录无法被发现
        ]  # 新增代码+RealChrome: 结束候选列表；若省略: Python 列表语法不完整

    def find_chrome_path(self) -> Path | None:  # 新增代码+RealChrome: 找到第一个存在的 chrome.exe；若省略: 上层只能自己重复候选检查
        return _existing_path(self.chrome_path_candidates())  # 新增代码+RealChrome: 复用存在性检查 helper；若省略: 函数不会返回发现到的 Chrome 路径

    def find_user_data_dir(self) -> Path | None:  # 新增代码+RealChrome: 找到第一个存在的 User Data 目录；若省略: 上层无法知道真实 profile 根目录是否存在
        return _existing_path(self.user_data_dir_candidates())  # 新增代码+RealChrome: 复用存在性检查 helper；若省略: 函数不会返回发现到的 profile 路径

    def chrome_is_running(self) -> bool:  # 新增代码+RealChrome: 检测当前是否已有 chrome.exe 运行；若省略: 可能在 profile 被占用时仍尝试启动
        command = ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV", "/NH"]  # 新增代码+RealChrome: 用 tasklist 精确过滤 chrome.exe；若省略: 测试无法确认命令包含安全的进程过滤条件
        fallback_command = ["powershell", "-NoProfile", "-Command", "if (Get-Process chrome -ErrorAction SilentlyContinue) { 'chrome.exe' }"]  # 修改代码+RealChromeTasklistFallback: tasklist 在受限环境被拒绝时用 Get-Process 复查；若没有这行代码，真实可见终端验收会把 Access denied 误判为 Chrome 正在运行
        try:  # 新增代码+RealChrome: 捕获系统命令缺失或执行失败；若省略: 非 Windows 或 tasklist 异常会中断诊断
            completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)  # 新增代码+RealChrome: 执行 tasklist 并读取文本输出；若省略: 无法知道 chrome.exe 是否在进程列表里
        except (OSError, subprocess.SubprocessError):  # 修改代码+RealChrome: 处理命令不可用、超时等异常；若省略: 环境差异会让 helper 直接报错
            return True  # 修改代码+RealChrome: 检测失败时按 Chrome 可能正在运行处理，避免误抢真实 profile；若省略: tasklist 故障会被误判成 Chrome 没运行
        if completed.returncode != 0:  # 新增代码+RealChrome: 把 tasklist 非零退出码视为检测失败；若省略: 命令执行失败但 stdout 为空会被误判成 Chrome 没运行
            try:  # 修改代码+RealChromeTasklistFallback: 只在 tasklist 失败后启动第二种本机进程检测；若没有这行代码，fallback 命令失败会直接冒泡中断 doctor
                fallback_completed = subprocess.run(fallback_command, capture_output=True, text=True, check=False, timeout=5)  # 修改代码+RealChromeTasklistFallback: 调用 PowerShell Get-Process chrome 并读取输出；若没有这行代码，受限 tasklist 环境没有第二证据来源
            except (OSError, subprocess.SubprocessError):  # 修改代码+RealChromeTasklistFallback: 捕获 fallback 命令不可用或超时；若没有这行代码，PowerShell 不可用时会让真实 Chrome 诊断崩溃
                return True  # 修改代码+RealChromeTasklistFallback: 双重检测都失败时继续偏安全处理；若没有这行代码，完全无法确认进程状态时可能误抢用户 profile
            if fallback_completed.returncode != 0:  # 修改代码+RealChromeTasklistFallback: fallback 自身失败仍视为无法确认；若没有这行代码，错误输出可能被当成无 Chrome
                return True  # 修改代码+RealChromeTasklistFallback: fallback 失败时保持安全优先；若没有这行代码，权限异常会被误判为 Chrome 未运行
            return "chrome.exe" in fallback_completed.stdout.lower()  # 修改代码+RealChromeTasklistFallback: fallback 没输出时表示未发现 Chrome；若没有这行代码，tasklist Access denied 会一直阻断真实终端验收
        return "chrome.exe" in completed.stdout.lower()  # 新增代码+RealChrome: 只要输出包含 chrome.exe 就认为 Chrome 正在运行；若省略: 测试模拟的 tasklist 结果不会被识别


def build_chrome_debug_command(chrome_path: Path, user_data_dir: Path, profile_directory: str, debug_port: int) -> list[str]:  # 新增代码+RealChrome: 构造安全的 Chrome CDP 启动参数列表；若省略: 上层可能拼出暴露到局域网的命令
    return [  # 新增代码+RealChrome: 返回参数列表而不是字符串，避免 shell 转义风险；若省略: 调用方无法直接安全传给 subprocess
        str(chrome_path),  # 新增代码+RealChrome: 命令第一项是 chrome.exe 路径；若省略: 系统不知道要启动哪个程序
        f"--user-data-dir={user_data_dir}",  # 新增代码+RealChrome: 指定真实 Chrome User Data 根目录；若省略: Chrome 可能使用临时或默认错误目录
        f"--profile-directory={profile_directory}",  # 新增代码+RealChrome: 指定具体 profile 子目录；若省略: 可能打开错误身份或默认 profile
        "--remote-debugging-address=127.0.0.1",  # 新增代码+RealChrome: 调试端口只绑定本机回环；若省略: CDP 端口可能被局域网设备访问
        f"--remote-debugging-port={debug_port}",  # 新增代码+RealChrome: 指定 CDP 调试端口；若省略: 自动化客户端不知道连接哪里
        "about:blank",  # 新增代码+RealChrome: 启动空白页减少恢复旧页面副作用；若省略: Chrome 可能恢复用户旧标签页造成干扰
    ]  # 新增代码+RealChrome: 结束命令列表；若省略: Python 列表语法不完整


def choose_loopback_port(preferred_port: int = 9222) -> int:  # 修改代码+RealChrome: 选择一个当前可用的本机回环端口，但返回后仍可能被其它进程抢占；若省略: 端口占用时 Chrome 调试启动会失败且后续 launcher 缺少重试提醒
    if _is_loopback_port_available(preferred_port):  # 新增代码+RealChrome: 优先使用调用方指定端口；若省略: 默认 9222 可用时也会随机变化，排查更困难
        return preferred_port  # 修改代码+RealChrome: 首选端口当前可用就直接返回，后续启动失败仍需要 launcher 重试；若省略: 测试无法确认可用端口被保留
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:  # 新增代码+RealChrome: 创建临时 socket 让系统分配空闲端口；若省略: 只能靠猜测下一个端口是否可用
        sock.bind(("127.0.0.1", 0))  # 新增代码+RealChrome: 绑定端口 0 表示让 OS 选空闲回环端口；若省略: 无法可靠避开已占用端口
        chosen_port = int(sock.getsockname()[1])  # 新增代码+RealChrome: 读取 OS 分配的真实端口号；若省略: 函数没有可返回的备用端口
    return chosen_port  # 修改代码+RealChrome: 关闭临时 socket 后返回端口给调用方再次绑定，TOCTOU 竞态由后续启动失败重试处理；若省略: 调用方拿不到备用端口


def wait_for_cdp_endpoint(port: int, timeout_seconds: float = 10.0) -> bool:  # 新增代码+RealChrome: 等待 Chrome CDP /json/version 可访问；若省略: 启动后可能在端点未就绪时立刻连接失败
    deadline = time.monotonic() + timeout_seconds  # 新增代码+RealChrome: 计算轮询截止时间；若省略: 函数可能无限等待或过早停止
    url = f"http://127.0.0.1:{port}/json/version"  # 新增代码+RealChrome: 只访问本机 CDP 版本端点；若省略: 无法验证指定端口是否提供 CDP
    while time.monotonic() < deadline:  # 新增代码+RealChrome: 在超时前持续尝试；若省略: 只能尝试一次，Chrome 慢启动时容易误判
        try:  # 新增代码+RealChrome: 捕获连接失败和 JSON 解析失败；若省略: CDP 未就绪会把异常抛给调用方
            with urllib.request.urlopen(url, timeout=1.0) as response:  # 新增代码+RealChrome: 请求 /json/version 并限制单次等待；若省略: 单次请求可能卡住整个等待流程
                version_payload = json.loads(response.read().decode("utf-8"))  # 修改代码+RealChrome: 解析响应 JSON 供字段校验；若省略: HTML 错误页也可能被误认为成功
            if _cdp_version_payload_is_trusted(version_payload, port):  # 修改代码+RealChrome: 校验 websocket 指向本机端口或 Browser 明确是 Chrome/Chromium；若省略: 只有 Protocol-Version 的任意 JSON 会误过
                return True  # 修改代码+RealChrome: 只有可信 Chrome/CDP 响应后才返回可用；若省略: 真实 CDP 就绪后调用方仍会等到超时
            time.sleep(0.1)  # 新增代码+RealChrome: JSON 合法但不像 Chrome/CDP 时短暂等待再试；若省略: 本地非 CDP JSON 服务会导致循环忙等占用 CPU
        except (OSError, urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError):  # 新增代码+RealChrome: 把网络和解析失败视为尚未就绪；若省略: 正常启动等待中的短暂失败会中断流程
            time.sleep(0.1)  # 新增代码+RealChrome: 短暂等待后重试，避免忙等占用 CPU；若省略: 循环会过度消耗资源
    return False  # 新增代码+RealChrome: 超时仍不可访问时返回失败；若省略: 调用方无法知道端点未就绪


class BrowserSafetyPolicy:  # 新增代码+RealChrome: 定义浏览器脚本安全策略；若省略: 自动化可能读取 cookie/token 等敏感登录态
    _function_constructor_patterns = (  # 新增代码+RealChrome: 定义 Function 构造器危险入口正则；若省略: 带空格或动态属性的 Function 构造器会漏拦
        re.compile(r"\b(?:new\s+)?Function\s*\("),  # 新增代码+RealChrome: 拦截 Function (...) 和 new Function (...)；若省略: 空白变体可绕过字符串精确匹配
        re.compile(r"\[\s*([\"'`])Function\1\s*\]"),  # 新增代码+RealChrome: 拦截 ["Function"]、['Function'] 和 [`Function`] 动态属性访问；若省略: globalThis["Function"] 可动态执行字符串代码
    )  # 新增代码+RealChrome: 结束 Function 构造器正则元组；若省略: Python 元组语法不完整
    _obfuscation_fragments = (  # 新增代码+RealChrome: 定义常见动态构造和混淆入口；若省略: \x、fromCharCode、eval 等可绕开简单敏感词检测
        "\\x",  # 新增代码+RealChrome: 拒绝十六进制字符串转义；若省略: document["\x63ookie"] 可隐藏 cookie 字样
        "fromcharcode",  # 新增代码+RealChrome: 拒绝 String.fromCharCode 和裸 fromCharCode；若省略: localStorage 可被动态拼出来
        "eval",  # 新增代码+RealChrome: 拒绝 eval 动态执行；若省略: 敏感读取可藏进运行时字符串
        "settimeout",  # 新增代码+RealChrome: 拒绝 setTimeout 字符串版动态执行入口；若省略: setTimeout("...") 可执行字符串代码
        "setinterval",  # 新增代码+RealChrome: 拒绝 setInterval 字符串版动态执行入口；若省略: setInterval("...") 可周期执行字符串代码
        "functioncall",  # 新增代码+RealChrome: 拒绝 Function.call 别名执行入口；若省略: Function.call(null, "...") 可绕过 Function( 检测
        "functionbind",  # 新增代码+RealChrome: 拒绝 Function.bind 别名执行入口；若省略: Function.bind(null, "...") 可绕过 Function( 检测
        "functionapply",  # 新增代码+RealChrome: 拒绝 Function.apply 别名执行入口；若省略: Function.apply(null, Array("...")) 可绕过 Function( 检测
        "reflectapply",  # 新增代码+RealChrome: 拒绝 Reflect.apply 动态执行入口；若省略: Reflect.apply(Function, null, Array("...")) 可间接执行字符串代码
        "reflectconstruct",  # 新增代码+RealChrome: 拒绝 Reflect.construct 动态执行入口；若省略: Reflect.construct(Function, Array("...")) 可间接创建执行函数
        "atob",  # 新增代码+RealChrome: 拒绝 base64 解码入口；若省略: 敏感脚本可编码后再执行
        "decodeuricomponent",  # 新增代码+RealChrome: 拒绝 URL 解码入口；若省略: 敏感字段可编码后绕过
        "unescape",  # 新增代码+RealChrome: 拒绝旧式解码入口；若省略: 敏感字段可用转义字符串绕过
        "constructor",  # 新增代码+RealChrome: 拒绝 constructor 链动态访问；若省略: 可绕到 Function 构造器
        "prototype",  # 新增代码+RealChrome: 拒绝 prototype 链访问；若省略: 可通过原型链做间接动态行为
        "__proto__",  # 新增代码+RealChrome: 拒绝 __proto__ 原型入口；若省略: 可通过原型链绕过静态检查
    )  # 新增代码+RealChrome: 结束混淆入口元组；若省略: Python 元组语法不完整
    _dynamic_property_risk_fragments = (  # 新增代码+RealChrome: 定义方括号动态属性访问时的风险词；若省略: document/window 上的敏感动态属性会被放过
        "document",  # 新增代码+RealChrome: 方括号访问 document 时偏安全拒绝；若省略: document["cookie"] 类访问可能漏掉
        "window",  # 新增代码+RealChrome: 方括号访问 window 时偏安全拒绝；若省略: window["localStorage"] 类访问可能漏掉
        "local",  # 新增代码+RealChrome: 捕捉 local + Storage 分段构造；若省略: 本地存储动态拼接可能漏掉
        "storage",  # 新增代码+RealChrome: 捕捉 storage 相关动态属性；若省略: localStorage/sessionStorage 变体可能漏掉
        "cookie",  # 新增代码+RealChrome: 捕捉 cookie 动态属性；若省略: cookie 读取可能漏掉
        "session",  # 新增代码+RealChrome: 捕捉 sessionStorage 分段构造；若省略: 会话存储动态拼接可能漏掉
        "password",  # 新增代码+RealChrome: 捕捉密码相关动态属性；若省略: 密码字段访问可能漏掉
        "token",  # 新增代码+RealChrome: 捕捉 token 相关动态属性；若省略: token 字段访问可能漏掉
        "secret",  # 新增代码+RealChrome: 捕捉 secret 相关动态属性；若省略: 密钥字段访问可能漏掉
    )  # 新增代码+RealChrome: 结束动态属性风险词元组；若省略: Python 元组语法不完整
    _blocked_fragments = (  # 修改代码+RealChrome: 保存规范化后要禁止的敏感片段；若省略: document["cookie"] 和拼接 localStorage 会绕过检查
        "documentcookie",  # 修改代码+RealChrome: 禁止 document.cookie 和 document["cookie"]；若省略: 脚本可能导出登录 cookie
        "localstorage",  # 修改代码+RealChrome: 禁止 localStorage 和 local + Storage 拼接；若省略: 脚本可能读取本地持久化 token
        "sessionstorage",  # 修改代码+RealChrome: 禁止 sessionStorage；若省略: 脚本可能读取当前会话数据
        "password",  # 修改代码+RealChrome: 禁止访问密码相关字段；若省略: 脚本可能读取密码输入框
        "authorization",  # 修改代码+RealChrome: 禁止鉴权头文本；若省略: 脚本可能暴露 Bearer token
        "setcookie",  # 修改代码+RealChrome: 禁止 Set-Cookie 文本；若省略: 脚本可能暴露服务端下发 cookie
        "token",  # 修改代码+RealChrome: 禁止 token 字样；若省略: 常见凭据变量可能被读取
        "secret",  # 修改代码+RealChrome: 禁止 secret 字样；若省略: 密钥类变量可能被读取
        "cookie",  # 修改代码+RealChrome: 禁止 cookie 字样作为兜底；若省略: document.cookie 之外的 cookie 访问可能漏掉
    )  # 修改代码+RealChrome: 结束敏感片段元组；若省略: Python 元组语法不完整

    def validate_script(self, script: str) -> None:  # 新增代码+RealChrome: 校验即将注入浏览器的脚本是否安全；若省略: 调用方无法在执行前拦截敏感脚本
        normalized_script = _normalize_sensitive_text(script)  # 新增代码+RealChrome: 规范化脚本以识别引号、点号、方括号和拼接混淆；若省略: document["cookie"] 这类写法会绕过
        lower_script = script.lower()  # 新增代码+RealChrome: 保留原始符号的小写脚本用于识别 \x、[] 等混淆符号；若省略: 规范化后会丢失关键混淆信号
        for pattern in self._function_constructor_patterns:  # 修改代码+RealChrome: 遍历 Function 构造器正则而不是简单字符串；若省略: Function 后带空白或动态属性访问会漏掉
            if pattern.search(script):  # 修改代码+RealChrome: 在原始脚本文本中大小写敏感匹配 Function 构造器；若省略: 普通小写 function 和危险大写 Function 无法区分
                raise RealChromeProfileError("脚本包含敏感内容，已拒绝执行: Function-constructor")  # 修改代码+RealChrome: Function 构造器可动态执行字符串代码所以拒绝；若省略: 危险动态执行脚本可能继续执行
        for fragment in self._obfuscation_fragments:  # 新增代码+RealChrome: 遍历常见混淆和动态执行入口；若省略: 动态构造敏感访问仍可能通过
            if fragment in lower_script or fragment in normalized_script:  # 新增代码+RealChrome: 同时检查原文和规范化文本；若省略: fromCharCode 或 \x 这类不同形态可能漏掉
                raise RealChromeProfileError(f"脚本包含敏感内容，已拒绝执行: {fragment}")  # 新增代码+RealChrome: 这不是完整 JS sandbox，只是保守拒绝混淆入口；若省略: 真实 profile 下会给人过强安全错觉
        if "[" in script and "]" in script:  # 新增代码+RealChrome: 方括号属性访问在真实 profile 下按高风险处理；若省略: document/window 动态属性访问可能绕过点号检查
            if "function" in normalized_script:  # 新增代码+RealChrome: 方括号动态属性里出现 split 后的 Function 也偏安全拒绝；若省略: globalThis["Fun"+"ction"] 可绕过 Function 构造器检测
                raise RealChromeProfileError("脚本包含敏感内容，已拒绝执行: dynamic-function")  # 新增代码+RealChrome: 拒绝动态 Function 属性访问，普通 function 声明因没有方括号仍可通过；若省略: split Function 构造器可继续执行
            for fragment in self._dynamic_property_risk_fragments:  # 新增代码+RealChrome: 检查方括号脚本是否伴随 document/window/cookie/token 等风险词；若省略: 只能粗暴拒绝全部方括号或漏掉风险词
                if fragment in normalized_script:  # 新增代码+RealChrome: 只要动态属性访问伴随风险词就拒绝；若省略: window["local"+"Storage"] 仍可能放行
                    raise RealChromeProfileError(f"脚本包含敏感内容，已拒绝执行: dynamic-{fragment}")  # 新增代码+RealChrome: 明确这是保守拒绝动态属性风险，最终执行层仍需要用户确认；若省略: 风险脚本会继续执行
        for fragment in self._blocked_fragments:  # 修改代码+RealChrome: 遍历规范化敏感片段；若省略: 只能检查一个固定风险
            if fragment in normalized_script:  # 修改代码+RealChrome: 在规范化脚本中匹配敏感片段；若省略: Token/TOKEN 或 local + Storage 变体可能绕过
                raise RealChromeProfileError(f"脚本包含敏感内容，已拒绝执行: {fragment}")  # 修改代码+RealChrome: 发现敏感脚本时抛专用错误；若省略: 风险脚本会继续执行


class BrowserAuditLogger:  # 新增代码+RealChrome: 提供浏览器自动化审计 JSONL 日志；若省略: 后续无法追踪真实 profile 自动化做过什么
    def __init__(self, path: Path) -> None:  # 新增代码+RealChrome: 接收审计日志文件路径；若省略: logger 不知道写到哪里
        self.path = path  # 新增代码+RealChrome: 保存日志路径供 record 使用；若省略: record 无法定位目标文件

    def record(self, event: str, details: dict[str, Any]) -> None:  # 新增代码+RealChrome: 写入一条审计事件；若省略: 调用方无法持久化自动化行为记录
        self.path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+RealChrome: 自动创建日志父目录；若省略: 首次写日志可能因目录不存在失败
        payload = {"event": event, "details": _redact_details(details)}  # 新增代码+RealChrome: 组装并清理敏感字段；若省略: 日志格式不统一且可能泄露敏感内容
        with self.path.open("a", encoding="utf-8") as handle:  # 新增代码+RealChrome: 以追加模式打开 JSONL 文件；若省略: 新事件可能覆盖旧审计记录
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")  # 新增代码+RealChrome: 写一行 JSON 并保留中文可读；若省略: 审计事件不会真正落盘


def diagnose_real_chrome_environment(workspace: str | Path) -> ChromeProfileDiagnostic:  # 新增代码+RealChrome: 诊断真实 Chrome profile 自动化环境；若省略: 用户无法获得结构化可行动提示
    _ = Path(workspace)  # 新增代码+RealChrome: 接受 workspace 参数并转成 Path 保持 API 形状；若省略: 调用方传参看起来没有被函数接收
    manager = ChromeProfileManager()  # 新增代码+RealChrome: 创建默认 Windows 路径管理器；若省略: 诊断无法检查 Chrome 路径和进程状态
    chrome_path = manager.find_chrome_path()  # 新增代码+RealChrome: 查找 chrome.exe；若省略: 诊断不知道浏览器是否安装
    user_data_dir = manager.find_user_data_dir()  # 新增代码+RealChrome: 查找 User Data 目录；若省略: 诊断不知道真实 profile 是否存在
    chrome_running = manager.chrome_is_running()  # 新增代码+RealChrome: 检查 Chrome 是否正在运行；若省略: 诊断无法提醒用户关闭 Chrome
    port_available = _is_loopback_port_available(9222)  # 新增代码+RealChrome: 检查默认 CDP 端口是否可用；若省略: 端口冲突不会提前暴露
    cdp_endpoint_available = (not port_available) and wait_for_cdp_endpoint(9222, timeout_seconds=1.0)  # 新增代码+RealChrome已有CDP诊断: 端口被占用时进一步确认占用者是否是可信 Chrome CDP；若省略: 可接管的已有 Chrome 会被误报为需要用户处理
    messages: list[str] = []  # 新增代码+RealChrome: 准备收集用户可读提示；若省略: 诊断结果缺少原因说明
    if chrome_path is None:  # 新增代码+RealChrome: 判断 chrome.exe 是否缺失；若省略: 缺浏览器也可能被误报可用
        messages.append("未找到 chrome.exe，请确认 Google Chrome 已安装。")  # 新增代码+RealChrome: 提示用户安装或检查 Chrome；若省略: blocked 状态缺少行动建议
    if user_data_dir is None:  # 新增代码+RealChrome: 判断 User Data 目录是否缺失；若省略: 缺 profile 根目录也可能被误报可用
        messages.append("未找到 Chrome User Data 目录，请先用 Chrome 登录并创建 profile。")  # 新增代码+RealChrome: 提示用户准备 profile；若省略: 用户不知道如何解除 blocked
    if chrome_running and cdp_endpoint_available:  # 新增代码+RealChrome已有CDP诊断: 已运行 Chrome 若已提供可信 CDP 就属于可接管状态；若省略: mcp-doctor 会继续误导用户关闭 Chrome
        messages.append("检测到 Chrome 正在运行，且默认调试端口 9222 已是可信 Chrome CDP，可直接连接已有可见 Chrome。")  # 新增代码+RealChrome已有CDP诊断: 解释为什么正在运行反而可用；若省略: 用户看不懂 status=available 的原因
    elif chrome_running:  # 修改代码+RealChrome已有CDP诊断: 只有没有可信 CDP 时才要求关闭 Chrome；若省略: profile 锁冲突不会被提示
        messages.append("检测到 Chrome 正在运行，请先关闭 Chrome 后再启动真实 profile 自动化。")  # 修改代码+RealChrome已有CDP诊断: 给出关闭 Chrome 的明确动作；若省略: needs_user_action 状态不够可执行
    if not port_available and cdp_endpoint_available:  # 新增代码+RealChrome已有CDP诊断: 区分“端口被 Chrome CDP 使用”和“端口被未知进程占用”；若省略: 可用端口会被误判为冲突
        messages.append("默认调试端口 9222 已被当前 Chrome CDP 使用，agent 会附着已有端口而不是启动新 Chrome。")  # 新增代码+RealChrome已有CDP诊断: 告诉用户不会新开或关闭浏览器；若省略: 端口占用提示会显得矛盾
    elif not port_available:  # 修改代码+RealChrome已有CDP诊断: 只有不是可信 CDP 的端口占用才提示冲突；若省略: 端口占用不会出现在诊断信息里
        messages.append("默认调试端口 9222 已被占用，启动前需要选择其他本机端口。")  # 新增代码+RealChrome: 提示端口冲突处理方向；若省略: 用户不知道为什么连接失败
    if chrome_path is None or user_data_dir is None:  # 新增代码+RealChrome: 路径缺失属于阻塞状态；若省略: 缺关键路径时可能继续启动并失败
        status = "blocked"  # 新增代码+RealChrome: 标记环境缺关键文件不可继续；若省略: 调用方无法阻止危险或必失败启动
    elif cdp_endpoint_available:  # 新增代码+RealChrome已有CDP诊断: 已有可信 CDP 时可直接附着，不需要用户关闭 Chrome；若省略: 真实可见 Chrome 验收会被状态层误拦截
        status = "available"  # 新增代码+RealChrome已有CDP诊断: 标记当前环境可连接已有 Chrome；若省略: 调用方无法区分可附着和需处理
    elif chrome_running or not port_available:  # 修改代码+RealChrome已有CDP诊断: 仅非 CDP 的运行中或端口占用才需要用户处理；若省略: 可修复问题会被误报 available
        status = "needs_user_action"  # 新增代码+RealChrome: 标记需要用户先关闭 Chrome 或换端口；若省略: UI 无法区分可用和需处理状态
    else:  # 新增代码+RealChrome: 没有阻塞和待处理问题时环境可用；若省略: 可用环境没有状态出口
        status = "available"  # 新增代码+RealChrome: 标记真实 Chrome 环境可以尝试启动；若省略: 成功路径没有明确结果
    return ChromeProfileDiagnostic(  # 新增代码+RealChrome: 返回结构化诊断对象；若省略: 调用方拿不到诊断结果
        status=status,  # 新增代码+RealChrome: 写入三态状态；若省略: 返回对象缺少核心判断
        chrome_path=str(chrome_path or ""),  # 新增代码+RealChrome: 写入 Chrome 路径或空字符串；若省略: 用户看不到检测结果
        user_data_dir=str(user_data_dir or ""),  # 新增代码+RealChrome: 写入 User Data 路径或空字符串；若省略: 用户看不到 profile 检测结果
        chrome_running=chrome_running,  # 新增代码+RealChrome: 写入进程检测结果；若省略: 调用方不知道是否需要关闭 Chrome
        port_available=port_available,  # 新增代码+RealChrome: 写入端口检测结果；若省略: 调用方不知道默认端口是否冲突
        messages=messages,  # 新增代码+RealChrome: 写入诊断提示列表；若省略: 用户不知道状态背后的原因
    )  # 新增代码+RealChrome: 结束诊断对象构造；若省略: Python 调用语法不完整
