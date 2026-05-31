"""浏览器产物文件名安全 helper。"""  # 新增代码+BrowserSplit: 把截图和下载文件名清理逻辑收拢到 browser 层；如果没有这行代码，产物路径安全规则会散落。
from pathlib import Path  # 新增代码+BrowserSplit: 使用 Path 处理跨平台路径；如果没有这行代码，文件名拼接会退回易错字符串。
import re  # 新增代码+BrowserSplit: 使用正则清理危险字符；如果没有这行代码，文件名安全过滤无法实现。

def sanitized_artifact_filename(raw_name: object, default_name: str) -> str:  # 新增代码+BrowserSplit: 把用户或浏览器提供的文件名清理成安全文件名；如果没有这行代码，MCP server 需要继续内联清理。
    fallback_text = str(default_name or "artifact").strip()  # 新增代码+BrowserSplit: 准备默认文件名兜底；如果没有这行代码，空默认名会导致无稳定目标。
    candidate_text = str(raw_name or "").strip() or fallback_text  # 新增代码+BrowserSplit: 优先使用原始名称，空值回退默认名；如果没有这行代码，用户不传文件名时会失败。
    safe_name = re.sub(r"[^A-Za-z0-9._ -]+", "_", candidate_text).strip(" .")  # 新增代码+BrowserSplit: 只保留常见跨平台安全字符；如果没有这行代码，控制字符或路径分隔符可能造成写入风险。
    if not safe_name or safe_name in {".", ".."}:  # 新增代码+BrowserSplit: 防御清理后变成空名或点目录；如果没有这行代码，目标可能退化成当前目录或父目录。
        safe_name = re.sub(r"[^A-Za-z0-9._ -]+", "_", fallback_text).strip(" .") or "artifact"  # 新增代码+BrowserSplit: 再清理默认名并最终兜底 artifact；如果没有这行代码，默认名异常时仍会失败。
    return safe_name  # 新增代码+BrowserSplit: 返回安全文件名；如果没有这行代码，调用方拿不到结果。

def safe_browser_artifact_path(artifacts_dir: Path, raw_name: object, default_name: str) -> Path:  # 新增代码+BrowserSplit: 把安全文件名解析到 browser_artifacts 内；如果没有这行代码，路径越界校验仍会分散。
    artifacts_root = Path(artifacts_dir).resolve()  # 新增代码+BrowserSplit: 解析产物目录真实路径；如果没有这行代码，符号链接或相对路径边界无法比较。
    target_path = (artifacts_root / sanitized_artifact_filename(raw_name, default_name)).resolve()  # 新增代码+BrowserSplit: 拼接并解析目标路径；如果没有这行代码，无法确认最终写入位置。
    try:  # 新增代码+BrowserSplit: 尝试确认目标仍在产物目录内；如果没有这行代码，越界文件名可能绕过目录边界。
        target_path.relative_to(artifacts_root)  # 新增代码+BrowserSplit: 核心越界校验；如果没有这行代码，恶意文件名可能写到工作区外。
    except ValueError:  # 新增代码+BrowserSplit: 捕获目标不在产物目录内的情况；如果没有这行代码，越界路径会继续使用。
        return (artifacts_root / "artifact").resolve()  # 新增代码+BrowserSplit: 越界时强制落回产物目录 artifact；如果没有这行代码，安全兜底失效。
    return target_path  # 新增代码+BrowserSplit: 返回目录内安全路径；如果没有这行代码，调用方拿不到可写目标。
