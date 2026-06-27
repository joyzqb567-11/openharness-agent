"""OpenHarness Provider 真实密钥泄漏扫描器。"""  # 新增代码+SecretLeakScanner：说明本脚本负责在真实 OAuth 开发前检查 token 泄漏；如果没有这行，维护者容易把它误当成普通 grep。

from __future__ import annotations  # 新增代码+SecretLeakScanner：启用延迟类型解析；如果没有这行，旧解释顺序下类型注解更脆弱。

import argparse  # 新增代码+SecretLeakScanner：解析命令行传入的扫描目录；如果没有这行，测试和人工运行无法指定临时目录。
import re  # 新增代码+SecretLeakScanner：用结构化正则识别真实 token 形状；如果没有这行，只能靠脆弱的字符串搜索。
import sys  # 新增代码+SecretLeakScanner：返回稳定进程退出码；如果没有这行，CI 无法根据扫描结果失败。
from dataclasses import dataclass  # 新增代码+SecretLeakScanner：用小数据类承载发现项；如果没有这行，错误输出会散落成多个元组字段。
from pathlib import Path  # 新增代码+SecretLeakScanner：跨 Windows 和测试临时目录处理路径；如果没有这行，路径拼接容易出错。
from typing import Iterable, Sequence  # 新增代码+SecretLeakScanner：标注可迭代输入边界；如果没有这行，函数输入形状不清楚。


PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 新增代码+SecretLeakScanner：定位仓库根目录；如果没有这行，默认扫描路径会随当前 shell 目录漂移。
DEFAULT_SCAN_ROOTS = (  # 新增代码+SecretLeakScanner：常规扫描范围段开始；如果没有这段，脚本可能误扫 node_modules 或漏扫运行代码。
    "agent_memory",  # 新增代码+SecretLeakScanner：扫描项目记忆，防止真实邮箱或 token 被长期写入；如果没有这行，复盘文件可能泄露用户信息。
    "memory",  # 新增代码+SecretLeakScanner：扫描运行状态目录，防止 GUI/OAuth 产物存 raw token；如果没有这行，最危险的落盘区会漏检。
    "apps/desktop/src",  # 新增代码+SecretLeakScanner：扫描桌面前端源码，防止把 token 写进 renderer；如果没有这行，前端泄漏不会被抓到。
    "learning_agent/app",  # 新增代码+SecretLeakScanner：扫描 GUI bridge/provider 后端源码；如果没有这行，后端日志和配置泄漏不被覆盖。
    "learning_agent/models",  # 新增代码+SecretLeakScanner：扫描模型适配层；如果没有这行，真实 Authorization 拼接泄漏不被覆盖。
    "learning_agent/scripts",  # 新增代码+SecretLeakScanner：扫描脚本目录，防止验收脚本硬编码密钥；如果没有这行，辅助脚本可能藏 token。
    "docs",  # 新增代码+SecretLeakScanner：扫描文档，防止蓝图或 runbook 粘贴真实 OAuth 值；如果没有这行，文档泄漏不会失败。
)  # 新增代码+SecretLeakScanner：常规扫描范围段结束；如果没有这行，Python 元组语法不完整。
SKIP_DIR_NAMES = {  # 新增代码+SecretLeakScanner：跳过目录集合段开始；如果没有这段，扫描会被依赖、缓存和学习副本噪声淹没。
    ".git",  # 新增代码+SecretLeakScanner：跳过 Git 内部对象；如果没有这行，历史对象会让扫描又慢又误报。
    ".worktrees",  # 新增代码+SecretLeakScanner：跳过兄弟 worktree；如果没有这行，当前分支会扫描到别的实验分支。
    "node_modules",  # 新增代码+SecretLeakScanner：跳过前端依赖；如果没有这行，扫描速度和误报都会失控。
    "__pycache__",  # 新增代码+SecretLeakScanner：跳过 Python 字节码缓存；如果没有这行，二进制缓存没有业务意义。
    ".pytest_cache",  # 新增代码+SecretLeakScanner：跳过 pytest 缓存；如果没有这行，旧失败文本可能污染结果。
    "dist",  # 新增代码+SecretLeakScanner：跳过构建产物；如果没有这行，前端 build 后重复扫描会变慢。
    "build",  # 新增代码+SecretLeakScanner：跳过构建产物；如果没有这行，打包文件会制造重复噪声。
    "coverage",  # 新增代码+SecretLeakScanner：跳过覆盖率报告；如果没有这行，HTML 报告可能重复源码字面量。
    "test",  # 新增代码+SecretLeakScanner：跳过学习备份目录 learning_agent/test；如果没有这行，历史证据副本会让新扫描不可用。
    "tests",  # 新增代码+SecretLeakScanner：跳过测试目录默认扫描；如果没有这行，测试用危险样本会被误当真实泄漏。
}  # 新增代码+SecretLeakScanner：跳过目录集合段结束；如果没有这行，集合语法不完整。
TEXT_SUFFIXES = {  # 新增代码+SecretLeakScanner：允许读取的文本后缀段开始；如果没有这段，脚本可能读取图片或二进制文件。
    ".css",  # 新增代码+SecretLeakScanner：覆盖前端样式文件；如果没有这行，样式内错误粘贴文本会漏检。
    ".json",  # 新增代码+SecretLeakScanner：覆盖状态和配置 JSON；如果没有这行，最常见的 token 落盘格式会漏检。
    ".log",  # 修改代码+SecretLeakScanner：覆盖 GUI、OAuth 和诊断日志；如果没有这行，memory/*.log 里的 Bearer token 或邮箱会被跳过。
    ".md",  # 新增代码+SecretLeakScanner：覆盖蓝图和 runbook；如果没有这行，文档粘贴 token 会漏检。
    ".mjs",  # 新增代码+SecretLeakScanner：覆盖 Node ESM 脚本；如果没有这行，视觉验收脚本会漏检。
    ".py",  # 新增代码+SecretLeakScanner：覆盖 Python 后端源码；如果没有这行，模型和 provider 代码会漏检。
    ".ps1",  # 新增代码+SecretLeakScanner：覆盖 PowerShell 启动脚本；如果没有这行，Windows 启动脚本泄漏会漏检。
    ".sse",  # 新增代码+SecretLeakScanner：覆盖 SSE fixture；如果没有这行，后续样本 drift 无法被发现。
    ".ts",  # 新增代码+SecretLeakScanner：覆盖 TypeScript 工具和 API；如果没有这行，前端 API 类型会漏检。
    ".tsx",  # 新增代码+SecretLeakScanner：覆盖 React 组件；如果没有这行，renderer UI 泄漏会漏检。
    ".txt",  # 新增代码+SecretLeakScanner：覆盖普通日志文本；如果没有这行，简单证据文件会漏检。
    ".yml",  # 新增代码+SecretLeakScanner：覆盖 YAML 配置；如果没有这行，CI 配置泄漏会漏检。
    ".yaml",  # 新增代码+SecretLeakScanner：覆盖 YAML 配置别名；如果没有这行，另一种后缀会漏检。
}  # 新增代码+SecretLeakScanner：允许读取的文本后缀段结束；如果没有这行，集合语法不完整。
DANGEROUS_PATTERNS = (  # 新增代码+SecretLeakScanner：危险 token 规则段开始；如果没有这段，脚本无法判断什么算真实泄漏。
    ("bearer_token", re.compile(r"Bearer\s+(?!test_)[A-Za-z0-9._~+\-/=]{32,}")),  # 新增代码+SecretLeakScanner：识别真实 Bearer token 形状但允许 test_；如果没有这行，OAuth access token 泄漏不会失败。
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),  # 新增代码+SecretLeakScanner：识别 OpenAI API key 形状；如果没有这行，sk- 密钥泄漏不会失败。
    ("jwt_like_token", re.compile(r"\b(?!test_)[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b")),  # 新增代码+SecretLeakScanner：识别三段 JWT 形状；如果没有这行，id_token 泄漏容易漏掉。
)  # 新增代码+SecretLeakScanner：危险 token 规则段结束；如果没有这行，元组语法不完整。
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")  # 新增代码+SecretLeakScanner：识别未脱敏邮箱；如果没有这行，account discovery 可能把真实邮箱写进日志。


@dataclass(frozen=True)  # 新增代码+SecretLeakScanner：让发现项不可变；如果没有这行，后续输出时发现项可能被误改。
class Finding:  # 新增代码+SecretLeakScanner：类段开始，承载一次泄漏发现；如果没有这个类，错误信息字段会变得难读。
    path: Path  # 新增代码+SecretLeakScanner：保存命中的文件路径；如果没有这行，用户无法定位泄漏来源。
    line_number: int  # 新增代码+SecretLeakScanner：保存命中行号；如果没有这行，修复时要人工重找。
    kind: str  # 新增代码+SecretLeakScanner：保存命中类型；如果没有这行，用户不知道是 token、key 还是邮箱。
    snippet: str  # 新增代码+SecretLeakScanner：保存脱敏片段；如果没有这行，排查不知道命中的大概上下文。
# 新增代码+SecretLeakScanner：类段结束，Finding 到此结束；如果没有边界说明，初学者不易看出它只是结果对象。


def _is_within_skipped_dir(path: Path) -> bool:  # 新增代码+SecretLeakScanner：函数段开始，判断路径是否在默认跳过目录里；如果没有这段，扫描会误进历史副本和依赖目录。
    return any(part in SKIP_DIR_NAMES for part in path.parts)  # 新增代码+SecretLeakScanner：逐级检查目录名；如果没有这行，Windows 深层路径跳过会失效。
# 新增代码+SecretLeakScanner：函数段结束，_is_within_skipped_dir 到此结束；如果没有边界说明，初学者不易看出它只做路径过滤。


def _is_fixture_path(path: Path) -> bool:  # 新增代码+SecretLeakScanner：函数段开始，判断是否是受控 fixture；如果没有这段，脱敏样本会被误判为真实泄漏。
    lower_parts = {part.lower() for part in path.parts}  # 新增代码+SecretLeakScanner：把路径片段转小写集合；如果没有这行，Windows 大小写差异可能误判。
    return "fixtures" in lower_parts or ("tests" in lower_parts and "fixtures" in lower_parts)  # 新增代码+SecretLeakScanner：允许测试 fixture 存放假 token 形状；如果没有这行，黄金样本无法覆盖真实 SSE 外形。
# 新增代码+SecretLeakScanner：函数段结束，_is_fixture_path 到此结束；如果没有边界说明，初学者不易看出它不是泛化白名单。


def _email_scan_required(path: Path) -> bool:  # 新增代码+SecretLeakScanner：函数段开始，判断这个文件是否需要邮箱泄漏检查；如果没有这段，源码里的示例邮箱会造成太多误报。
    lower_parts = {part.lower() for part in path.parts}  # 新增代码+SecretLeakScanner：收集小写路径片段；如果没有这行，memory/agent_memory 判断不稳定。
    lower_name = path.name.lower()  # 新增代码+SecretLeakScanner：读取小写文件名；如果没有这行，日志和诊断文件名判断不稳定。
    if "memory" in lower_parts or "agent_memory" in lower_parts:  # 新增代码+SecretLeakScanner：memory 区域最容易保存真实用户资料；如果没有这行，用户邮箱可能长期落盘。
        return True  # 新增代码+SecretLeakScanner：memory 区域必须检查邮箱；如果没有这行，函数会继续走普通文件名规则。
    return any(marker in lower_name for marker in ("log", "diagnostic", "diagnostics", "capture", "evidence", "trace"))  # 新增代码+SecretLeakScanner：日志/诊断/证据文件也检查邮箱；如果没有这行，GUI 验收截图摘要可能泄露账号。
# 新增代码+SecretLeakScanner：函数段结束，_email_scan_required 到此结束；如果没有边界说明，初学者不易看出它是高风险文件限定。


def _safe_snippet(text: str) -> str:  # 新增代码+SecretLeakScanner：函数段开始，把命中片段脱敏后输出；如果没有这段，扫描器自己会把 token 打印到终端。
    compact = text.strip().replace("\t", " ")  # 新增代码+SecretLeakScanner：压平制表符便于阅读；如果没有这行，输出可能错位。
    if len(compact) <= 18:  # 新增代码+SecretLeakScanner：短文本可以整体显示；如果没有这行，普通字段名也会被过度截断。
        return compact  # 新增代码+SecretLeakScanner：返回短片段；如果没有这行，用户无法看到命中类别附近文字。
    return f"{compact[:8]}...[redacted]...{compact[-6:]}"  # 新增代码+SecretLeakScanner：只保留极短前后缀；如果没有这行，真实 token 可能二次泄漏。
# 新增代码+SecretLeakScanner：函数段结束，_safe_snippet 到此结束；如果没有边界说明，初学者不易看出它保护输出安全。


def iter_scan_files(roots: Sequence[Path]) -> Iterable[Path]:  # 新增代码+SecretLeakScanner：函数段开始，生成需要检查的文本文件；如果没有这段，扫描目录遍历逻辑会重复。
    for root in roots:  # 新增代码+SecretLeakScanner：逐个处理用户或默认传入的根路径；如果没有这行，多目录扫描不可用。
        if not root.exists():  # 新增代码+SecretLeakScanner：容忍当前项目暂时没有 memory 目录；如果没有这行，首次运行会因为缺目录失败。
            continue  # 新增代码+SecretLeakScanner：跳过不存在路径；如果没有这行，默认扫描不稳。
        if root.is_file():  # 新增代码+SecretLeakScanner：支持直接传入单个文件；如果没有这行，单文件调试不方便。
            if root.suffix.lower() in TEXT_SUFFIXES:  # 新增代码+SecretLeakScanner：只读取已知文本文件；如果没有这行，二进制文件可能解码失败。
                yield root  # 新增代码+SecretLeakScanner：产出单个文本文件；如果没有这行，文件模式没有结果。
            continue  # 新增代码+SecretLeakScanner：文件路径处理完毕；如果没有这行，后续会把文件当目录遍历。
        for candidate in root.rglob("*"):  # 新增代码+SecretLeakScanner：递归遍历目录；如果没有这行，深层运行状态不会被扫描。
            if not candidate.is_file():  # 新增代码+SecretLeakScanner：跳过目录和特殊节点；如果没有这行，读取目录会失败。
                continue  # 新增代码+SecretLeakScanner：继续看下一个路径；如果没有这行，非文件会进入后缀判断。
            if _is_within_skipped_dir(candidate.relative_to(root)):  # 新增代码+SecretLeakScanner：跳过依赖、缓存、测试和学习副本；如果没有这行，扫描会大量误报。
                continue  # 新增代码+SecretLeakScanner：跳过当前候选文件；如果没有这行，跳过规则无效。
            if candidate.suffix.lower() not in TEXT_SUFFIXES:  # 新增代码+SecretLeakScanner：过滤非文本后缀；如果没有这行，图片和二进制会解码报错。
                continue  # 新增代码+SecretLeakScanner：继续看下一个候选文件；如果没有这行，非文本会被读取。
            yield candidate  # 新增代码+SecretLeakScanner：产出安全文本候选；如果没有这行，目录扫描不会返回文件。
# 新增代码+SecretLeakScanner：函数段结束，iter_scan_files 到此结束；如果没有边界说明，初学者不易看出它只负责找文件。


def scan_file(path: Path) -> list[Finding]:  # 新增代码+SecretLeakScanner：函数段开始，扫描单个文件内容；如果没有这段，CLI 无法形成可测试核心逻辑。
    findings: list[Finding] = []  # 新增代码+SecretLeakScanner：收集该文件全部发现项；如果没有这行，扫描结果无处保存。
    try:  # 新增代码+SecretLeakScanner：保护文本读取；如果没有这行，单个坏编码文件会让整次扫描中断。
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()  # 新增代码+SecretLeakScanner：按 UTF-8 宽容读取文本行；如果没有这行，无法逐行定位。
    except OSError as error:  # 新增代码+SecretLeakScanner：捕获文件消失或权限异常；如果没有这行，临时文件竞态会中断扫描。
        return [Finding(path=path, line_number=0, kind="read_error", snippet=_safe_snippet(str(error)))]  # 新增代码+SecretLeakScanner：把读取失败作为发现项返回；如果没有这行，用户不知道哪个文件读不了。
    fixture_path = _is_fixture_path(path)  # 新增代码+SecretLeakScanner：缓存 fixture 判断；如果没有这行，每条规则都会重复算路径。
    email_required = _email_scan_required(path)  # 新增代码+SecretLeakScanner：缓存邮箱扫描判断；如果没有这行，每行都会重复算路径类别。
    for index, line in enumerate(lines, start=1):  # 新增代码+SecretLeakScanner：逐行扫描并保留一基行号；如果没有这行，命中无法定位。
        if not fixture_path:  # 新增代码+SecretLeakScanner：fixture 以外才拦截真实形状 token；如果没有这行，黄金样本无法表达真实 SSE/JWT 外形。
            for kind, pattern in DANGEROUS_PATTERNS:  # 新增代码+SecretLeakScanner：逐条应用危险规则；如果没有这行，token/key/JWT 不会被检查。
                match = pattern.search(line)  # 新增代码+SecretLeakScanner：查找当前行是否命中；如果没有这行，规则不会执行。
                if match:  # 新增代码+SecretLeakScanner：只有命中才记录；如果没有这行，所有行都会误报。
                    findings.append(Finding(path=path, line_number=index, kind=kind, snippet=_safe_snippet(match.group(0))))  # 新增代码+SecretLeakScanner：保存脱敏命中；如果没有这行，失败报告没有证据。
        if email_required:  # 新增代码+SecretLeakScanner：只在高风险文件里检查邮箱；如果没有这行，源码示例邮箱会误报。
            email_match = EMAIL_PATTERN.search(line)  # 新增代码+SecretLeakScanner：查找未脱敏邮箱；如果没有这行，account 邮箱泄漏不会被发现。
            if email_match:  # 新增代码+SecretLeakScanner：命中邮箱才记录；如果没有这行，所有高风险行都会误报。
                findings.append(Finding(path=path, line_number=index, kind="email_address", snippet=_safe_snippet(email_match.group(0))))  # 新增代码+SecretLeakScanner：保存脱敏邮箱命中；如果没有这行，用户不知道哪个文件有邮箱。
    return findings  # 新增代码+SecretLeakScanner：返回该文件所有发现项；如果没有这行，调用方永远以为扫描通过。
# 新增代码+SecretLeakScanner：函数段结束，scan_file 到此结束；如果没有边界说明，初学者不易看出它是核心扫描函数。


def scan_paths(paths: Sequence[Path]) -> list[Finding]:  # 新增代码+SecretLeakScanner：函数段开始，扫描多个根路径；如果没有这段，CLI 和测试都要重复聚合逻辑。
    findings: list[Finding] = []  # 新增代码+SecretLeakScanner：保存所有文件的发现项；如果没有这行，跨文件结果无处累计。
    for file_path in iter_scan_files(paths):  # 新增代码+SecretLeakScanner：遍历候选文本文件；如果没有这行，多文件扫描不会发生。
        findings.extend(scan_file(file_path))  # 新增代码+SecretLeakScanner：追加单文件扫描结果；如果没有这行，发现项会被丢弃。
    return findings  # 新增代码+SecretLeakScanner：返回总发现项；如果没有这行，CLI 不能决定退出码。
# 新增代码+SecretLeakScanner：函数段结束，scan_paths 到此结束；如果没有边界说明，初学者不易看出它只负责聚合。


def _default_paths() -> list[Path]:  # 新增代码+SecretLeakScanner：函数段开始，构造默认扫描路径；如果没有这段，默认 CLI 入口无法工作。
    return [PROJECT_ROOT / relative_path for relative_path in DEFAULT_SCAN_ROOTS]  # 新增代码+SecretLeakScanner：把相对路径转成绝对路径；如果没有这行，从子目录运行会扫错位置。
# 新增代码+SecretLeakScanner：函数段结束，_default_paths 到此结束；如果没有边界说明，初学者不易看出它只负责默认路径。


def build_parser() -> argparse.ArgumentParser:  # 新增代码+SecretLeakScanner：函数段开始，创建命令行解析器；如果没有这段，脚本参数不可测试。
    parser = argparse.ArgumentParser(description="Scan OpenHarness provider files for real OAuth/API secret leaks.")  # 新增代码+SecretLeakScanner：声明脚本用途；如果没有这行，--help 不清楚。
    parser.add_argument("paths", nargs="*", help="Optional files or directories to scan. Defaults to OpenHarness high-risk paths.")  # 新增代码+SecretLeakScanner：允许测试传临时目录；如果没有这行，只能扫真实仓库。
    return parser  # 新增代码+SecretLeakScanner：返回解析器；如果没有这行，main 无法解析参数。
# 新增代码+SecretLeakScanner：函数段结束，build_parser 到此结束；如果没有边界说明，初学者不易看出它只负责 CLI。


def main(argv: Sequence[str] | None = None) -> int:  # 新增代码+SecretLeakScanner：函数段开始，执行命令行扫描；如果没有这段，脚本不能被 CI 直接调用。
    parser = build_parser()  # 新增代码+SecretLeakScanner：创建参数解析器；如果没有这行，无法读取用户传入路径。
    args = parser.parse_args(argv)  # 新增代码+SecretLeakScanner：解析参数；如果没有这行，argv 不会生效。
    roots = [Path(value).expanduser().resolve() for value in args.paths] if args.paths else _default_paths()  # 新增代码+SecretLeakScanner：选择用户路径或默认路径；如果没有这行，测试无法隔离扫描目标。
    findings = scan_paths(roots)  # 新增代码+SecretLeakScanner：执行实际扫描；如果没有这行，脚本只解析参数不检查文件。
    if findings:  # 新增代码+SecretLeakScanner：发现泄漏时进入失败输出；如果没有这行，泄漏也会返回成功。
        print("Provider secret leak scan failed.")  # 新增代码+SecretLeakScanner：输出失败摘要；如果没有这行，用户看不出扫描失败。
        for finding in findings:  # 新增代码+SecretLeakScanner：逐条打印发现项；如果没有这行，用户无法定位问题。
            display_path = finding.path if finding.path.is_absolute() else finding.path.resolve()  # 新增代码+SecretLeakScanner：规范化显示路径；如果没有这行，相对路径可能难以点击定位。
            print(f"{display_path}:{finding.line_number}: {finding.kind}: {finding.snippet}")  # 新增代码+SecretLeakScanner：打印脱敏发现；如果没有这行，失败报告没有具体证据。
        return 1  # 新增代码+SecretLeakScanner：泄漏时返回失败码；如果没有这行，CI 会误判通过。
    print("Provider secret leak scan passed.")  # 新增代码+SecretLeakScanner：输出蓝图要求的成功文本；如果没有这行，人工验收不知道扫描已通过。
    return 0  # 新增代码+SecretLeakScanner：无发现时返回成功码；如果没有这行，CI 无法判断成功。
# 新增代码+SecretLeakScanner：函数段结束，main 到此结束；如果没有边界说明，初学者不易看出它是 CLI 总入口。


if __name__ == "__main__":  # 新增代码+SecretLeakScanner：脚本直接运行入口；如果没有这行，python 文件不会执行 main。
    sys.exit(main())  # 新增代码+SecretLeakScanner：把 main 结果作为进程退出码；如果没有这行，失败扫描不会让命令失败。
