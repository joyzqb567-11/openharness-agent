"""本地 browser/search MCP server，用来给 learning_agent 提供通用联网搜索和网页读取能力。"""  # 新增代码: 说明这个文件是 MCP server；若省略: 初学者打开文件时不容易判断它和 agent 主程序的关系

from __future__ import annotations  # 新增代码: 允许类型注解在运行时延迟解析；若省略: 某些前向类型写法在旧环境中可能更脆弱

import json  # 新增代码: 读写 MCP 使用的单行 JSON-RPC 消息；若省略: server 无法解析客户端请求或返回响应
import re  # 新增代码: 归一化网页正文里的连续空白；若省略: fetch_url 返回内容会夹杂大量换行和空格
import sys  # 新增代码: 从 stdin 读取 MCP 请求并向 stdout 写响应；若省略: server 无法作为 stdio MCP 进程工作
import urllib.error  # 新增代码: 捕获 URL 请求失败异常；若省略: 网络错误会以底层异常形式泄漏
import urllib.parse  # 新增代码: 编码搜索词并解析 DuckDuckGo 跳转链接；若省略: 中文搜索和结果链接还原都会不可靠
import urllib.request  # 新增代码: 使用 Python 标准库发起网页请求；若省略: 当前没有 npm/npx 时就无法实现联网搜索
from html.parser import HTMLParser  # 新增代码: 用标准 HTML 解析器提取链接和正文；若省略: 只能用脆弱的字符串切割处理网页
from typing import Any  # 新增代码: 标注 JSON 字典和 MCP 参数的通用类型；若省略: 类型提示会更难读


if hasattr(sys.stdin, "reconfigure"):  # 新增代码+Windows编码修复: 检查当前 stdin 是否支持重新设置编码；若省略: 旧 Python 环境可能没有 reconfigure 方法
    sys.stdin.reconfigure(encoding="utf-8")  # 新增代码+Windows编码修复: 强制 MCP 输入按 UTF-8 读取；若省略: 中文 JSON 参数在 Windows 管道里可能乱码
if hasattr(sys.stdout, "reconfigure"):  # 新增代码+Windows编码修复: 检查当前 stdout 是否支持重新设置编码；若省略: 旧 Python 环境可能没有 reconfigure 方法
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")  # 新增代码+Windows编码修复: 强制 MCP 输出按 UTF-8 写出；若省略: client 按 UTF-8 解码中文 tools/list 时会失败


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LearningAgentBrowserSearchMCP/0.1"  # 新增代码: 给网页请求设置正常 User-Agent；若省略: 部分网站会拒绝默认 Python 请求
REQUEST_TIMEOUT_SECONDS = 12  # 新增代码: 限制单次网络请求最长等待时间；若省略: 网站无响应时 MCP 工具可能长时间卡住
MAX_RAW_BYTES = 1_000_000  # 新增代码: 限制最多读取 1MB 原始网页；若省略: 大页面可能占用过多内存并拖慢 agent
DEFAULT_MAX_CHARS = 6000  # 新增代码: 限制默认返回给模型的正文长度；若省略: 大网页会快速消耗模型上下文


TOOLS: list[dict[str, Any]] = [  # 新增代码: 定义这个 MCP server 暴露给 learning_agent 的工具列表；若省略: tools/list 无法告诉模型有哪些外部能力
    {  # 新增代码: 定义 web_search 工具对象；若省略: 模型无法通过 MCP 做通用网页搜索
        "name": "web_search",  # 新增代码: MCP 原始工具名；若省略: learning_agent 无法生成 mcp__browser_search__web_search
        "description": "联网搜索网页，返回若干搜索结果标题和链接，适合查询天气、新闻、文档等实时信息；这不是可见浏览器，也不是真实浏览器/真实 Chrome/登录态 workflow，用户明确要求真实浏览器时不能用它替代。",  # 修改代码+PromptSurfaceV2: 告诉模型搜索不是可见真实浏览器；若没有这行代码，模型可能用搜索结果替代用户要求的真实浏览器操作
        "inputSchema": {  # 新增代码: 声明 web_search 的参数 JSON Schema；若省略: 模型不知道该传入哪些参数
            "type": "object",  # 新增代码: 声明参数整体是对象；若省略: 参数格式不够明确
            "properties": {  # 新增代码: 列出可用参数字段；若省略: 模型无法看到字段说明
                "query": {  # 新增代码: 定义搜索关键词字段；若省略: 工具不知道要搜索什么
                    "type": "string",  # 新增代码: 声明 query 必须是字符串；若省略: 模型可能传入错误类型
                    "description": "要搜索的关键词，例如：宁波 鄞州区 今日天气。",  # 新增代码: 给模型提供中文参数示例；若省略: 模型可能构造不清晰的查询词
                },  # 新增代码: query 字段定义结束；若省略: JSON Schema 语法不完整
                "max_results": {  # 新增代码: 定义最多返回结果数；若省略: 用户无法控制搜索结果数量
                    "type": "integer",  # 新增代码: 声明 max_results 是整数；若省略: 模型可能传入字符串导致转换不稳定
                    "description": "最多返回多少条搜索结果，默认 5，建议 3 到 8。",  # 新增代码: 告诉模型合理范围；若省略: 模型可能请求过多结果
                },  # 新增代码: max_results 字段定义结束；若省略: JSON Schema 语法不完整
            },  # 新增代码: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["query"],  # 新增代码: 声明 query 必填；若省略: 模型可能调用空搜索
        },  # 新增代码: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码: web_search 工具对象结束；若省略: TOOLS 列表语法不完整
    {  # 新增代码: 定义 fetch_url 工具对象；若省略: 模型只能看到搜索结果，不能读取具体网页内容
        "name": "fetch_url",  # 新增代码: MCP 原始工具名；若省略: learning_agent 无法生成 mcp__browser_search__fetch_url
        "description": "读取指定 http/https 网页并提取正文文本，适合打开搜索结果链接继续获取细节；这不是可见浏览器，也不是真实浏览器/真实 Chrome/登录态 workflow，用户明确要求真实浏览器时不能用它替代。",  # 修改代码+PromptSurfaceV2: 告诉模型 fetch_url 只是正文读取不是可见浏览器；若没有这行代码，模型可能用静态网页读取冒充打开真实浏览器
        "inputSchema": {  # 新增代码: 声明 fetch_url 的参数 JSON Schema；若省略: 模型不知道如何传 URL
            "type": "object",  # 新增代码: 声明参数整体是对象；若省略: 参数格式不够明确
            "properties": {  # 新增代码: 列出 fetch_url 可用字段；若省略: 模型无法看到字段说明
                "url": {  # 新增代码: 定义要读取的网址字段；若省略: 工具没有目标网页
                    "type": "string",  # 新增代码: 声明 url 必须是字符串；若省略: 模型可能传入非字符串
                    "description": "要读取的 http 或 https 网页地址。",  # 新增代码: 告诉模型 URL 的限制；若省略: 模型可能传入本地路径或无效地址
                },  # 新增代码: url 字段定义结束；若省略: JSON Schema 语法不完整
                "max_chars": {  # 新增代码: 定义最多返回字符数；若省略: 无法限制长网页输出
                    "type": "integer",  # 新增代码: 声明 max_chars 是整数；若省略: 类型约束不明确
                    "description": "最多返回多少个字符，默认 6000。",  # 新增代码: 告诉模型默认截断策略；若省略: 模型不知道为什么网页内容会被截断
                },  # 新增代码: max_chars 字段定义结束；若省略: JSON Schema 语法不完整
            },  # 新增代码: properties 定义结束；若省略: JSON Schema 语法不完整
            "required": ["url"],  # 新增代码: 声明 url 必填；若省略: 模型可能调用空读取
        },  # 新增代码: inputSchema 定义结束；若省略: 工具定义不完整
    },  # 新增代码: fetch_url 工具对象结束；若省略: TOOLS 列表语法不完整
]  # 新增代码: TOOLS 列表结束；若省略: Python 语法不完整


class LinkCollector(HTMLParser):  # 新增代码: 从搜索结果 HTML 中收集链接；若省略: web_search 无法把 HTML 转成结果列表
    def __init__(self) -> None:  # 新增代码: 初始化链接收集器；若省略: 解析器没有保存状态的位置
        super().__init__()  # 新增代码: 初始化 HTMLParser 父类；若省略: 解析器内部状态可能不完整
        self.links: list[tuple[str, str]] = []  # 新增代码: 保存收集到的标题和 URL；若省略: 搜索结果无法返回给调用方
        self._active_href = ""  # 新增代码: 保存当前正在解析的 a 标签 href；若省略: handle_data 不知道文本属于哪个链接
        self._active_text_parts: list[str] = []  # 新增代码: 保存当前链接的文本片段；若省略: 多段标题文本无法合并

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # 新增代码: 处理 HTML 开始标签；若省略: 解析器无法发现链接 href
        if tag.lower() != "a":  # 新增代码: 只关心 a 标签；若省略: 其他标签会错误影响链接状态
            return  # 新增代码: 非链接标签直接跳过；若省略: 后续逻辑会对无关标签运行
        attrs_dict = {name.lower(): value or "" for name, value in attrs}  # 新增代码: 把属性列表转成字典；若省略: 获取 href 会更繁琐且容易漏空值
        self._active_href = attrs_dict.get("href", "")  # 新增代码: 保存当前链接地址；若省略: 链接文本无法对应 URL
        self._active_text_parts = []  # 新增代码: 新链接开始时清空标题片段；若省略: 上一个链接文本会污染当前链接

    def handle_data(self, data: str) -> None:  # 新增代码: 处理标签里的文本；若省略: 链接标题无法被收集
        if self._active_href:  # 新增代码: 只有处于 a 标签内才收集文本；若省略: 页面所有文本都会进入链接标题
            self._active_text_parts.append(data)  # 新增代码: 保存当前链接的一段文本；若省略: 最终标题会为空

    def handle_endtag(self, tag: str) -> None:  # 新增代码: 处理 HTML 结束标签；若省略: 无法在 a 标签结束时提交链接
        if tag.lower() != "a" or not self._active_href:  # 新增代码: 只有当前链接结束时才提交结果；若省略: 非链接标签会误触发提交
            return  # 新增代码: 无关结束标签直接跳过；若省略: 后续会处理错误状态
        title = normalize_spaces(" ".join(self._active_text_parts))  # 新增代码: 合并并清理链接标题；若省略: 标题会包含杂乱空白
        url = normalize_search_href(self._active_href)  # 新增代码: 把 DuckDuckGo 跳转链接还原成真实 URL；若省略: 用户只能看到搜索引擎中转地址
        if title and url and not should_skip_search_title(title):  # 新增代码: 只保留有效标题和有效 URL；若省略: 下一页、广告或空结果可能混入列表
            self.links.append((title, url))  # 新增代码: 保存一个搜索结果；若省略: web_search 最终没有结果可返回
        self._active_href = ""  # 新增代码: 清空当前链接地址；若省略: 后续普通文本可能被误认为链接文本
        self._active_text_parts = []  # 新增代码: 清空当前链接文本；若省略: 下一个链接可能继承旧标题


class TextExtractor(HTMLParser):  # 新增代码: 从 HTML 页面提取可读正文；若省略: fetch_url 只能返回原始 HTML
    def __init__(self) -> None:  # 新增代码: 初始化正文提取器；若省略: 无法保存解析过程中的文本片段
        super().__init__()  # 新增代码: 初始化 HTMLParser 父类；若省略: 解析器内部状态可能不完整
        self.parts: list[str] = []  # 新增代码: 保存正文文本片段；若省略: 无处累积网页内容
        self._skip_depth = 0  # 新增代码: 记录当前是否在 script/style 等应跳过区域；若省略: 脚本和样式会污染正文

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # 新增代码: 处理开始标签以识别跳过区域；若省略: 无法过滤 script/style
        if tag.lower() in {"script", "style", "noscript", "svg"}:  # 新增代码: 这些标签通常不是用户要读的正文；若省略: 返回内容会包含大量无用代码
            self._skip_depth += 1  # 新增代码: 进入跳过区域并支持嵌套；若省略: 嵌套标签可能提前恢复收集

    def handle_endtag(self, tag: str) -> None:  # 新增代码: 处理结束标签以离开跳过区域；若省略: 一旦进入 script/style 就可能永远不收集正文
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth > 0:  # 新增代码: 只在对应区域内减少深度；若省略: 普通结束标签可能破坏跳过状态
            self._skip_depth -= 1  # 新增代码: 离开一层跳过区域；若省略: 后续正文仍会被跳过

    def handle_data(self, data: str) -> None:  # 新增代码: 处理页面文本；若省略: 无法提取正文
        if self._skip_depth == 0:  # 新增代码: 只在非脚本样式区域收集文本；若省略: 无用代码会进入正文
            text = normalize_spaces(data)  # 新增代码: 清理当前文本片段空白；若省略: 返回内容会有杂乱空格
            if text:  # 新增代码: 只保留非空片段；若省略: parts 中会有大量空字符串
                self.parts.append(text)  # 新增代码: 保存正文片段；若省略: fetch_url 返回内容会为空

    def text(self) -> str:  # 新增代码: 返回合并后的正文文本；若省略: 调用方需要知道内部 parts 结构
        return normalize_spaces("\n".join(self.parts))  # 新增代码: 用换行合并片段并最终清理空白；若省略: 正文格式会更乱


def normalize_spaces(value: str) -> str:  # 新增代码: 统一清理字符串空白；若省略: 多处需要重复写正则清理逻辑
    return re.sub(r"\s+", " ", value).strip()  # 新增代码: 把连续空白压成一个空格并去掉两端空白；若省略: 搜索结果和正文不易读


def should_skip_search_title(title: str) -> bool:  # 新增代码: 判断搜索链接标题是否应跳过；若省略: 搜索结果里可能出现翻页和站内链接
    lowered = title.strip().lower()  # 新增代码: 小写化便于比较；若省略: 大小写不同的跳过词无法识别
    return lowered in {"next", "next page", "previous", "privacy", "feedback"}  # 新增代码: 跳过常见非结果链接；若省略: 这些链接可能污染搜索结果


def normalize_search_href(href: str) -> str:  # 新增代码: 把搜索结果 href 规范化成真实 URL；若省略: web_search 返回链接可能无法直接 fetch
    raw_href = href.strip()  # 新增代码: 去掉 href 两端空白；若省略: URL 解析可能失败
    if not raw_href:  # 新增代码: 处理空 href；若省略: 空链接可能继续解析
        return ""  # 新增代码: 空 href 不产生结果；若省略: 后续可能返回无效 URL
    if raw_href.startswith("//"):  # 新增代码: 处理协议相对 URL；若省略: //duckduckgo.com/l/... 无法被 urlparse 识别为 https
        raw_href = "https:" + raw_href  # 新增代码: 默认使用 https 协议；若省略: 结果链接缺少协议
    if raw_href.startswith("/"):  # 新增代码: 处理 DuckDuckGo 站内相对路径；若省略: /l/?uddg=... 无法解析出真实链接
        raw_href = "https://duckduckgo.com" + raw_href  # 新增代码: 补全 DuckDuckGo 域名；若省略: parse_qs 找不到完整查询参数
    parsed = urllib.parse.urlparse(raw_href)  # 新增代码: 解析 URL 结构；若省略: 无法判断域名和查询参数
    query = urllib.parse.parse_qs(parsed.query)  # 新增代码: 解析 URL 查询参数；若省略: 无法从 uddg 取出真实结果 URL
    if "uddg" in query and query["uddg"]:  # 新增代码: DuckDuckGo 结果常把真实 URL 放在 uddg；若省略: 返回的是跳转链接而不是真实网页
        return query["uddg"][0]  # 新增代码: 返回解码后的真实 URL；若省略: fetch_url 可能读到搜索中转页
    if parsed.scheme in {"http", "https"} and "duckduckgo.com" not in parsed.netloc.lower():  # 新增代码: 接受非 DuckDuckGo 的真实网页链接；若省略: 普通结果链接会被丢弃
        return raw_href  # 新增代码: 返回可直接访问的结果 URL；若省略: 有效链接不会出现在搜索结果中
    return ""  # 新增代码: 其他站内链接不作为搜索结果；若省略: 翻页或设置链接可能进入结果


def clamp_int(value: Any, default: int, minimum: int, maximum: int) -> int:  # 新增代码: 把模型传入的数字参数限制在安全范围；若省略: 模型可能请求过大输出
    try:  # 新增代码: 捕获无法转换为整数的参数；若省略: 坏参数会让工具调用崩溃
        number = int(value)  # 新增代码: 把字符串或数字转换成 int；若省略: JSON 里的数字类型不统一时不好处理
    except (TypeError, ValueError):  # 新增代码: 处理 None、对象、非数字字符串；若省略: 参数错误会泄漏底层异常
        number = default  # 新增代码: 使用默认值保持工具可用；若省略: 小错误会导致整次工具失败
    return max(minimum, min(maximum, number))  # 新增代码: 把数字夹在安全范围内；若省略: 过大或过小值可能影响稳定性


def fetch_raw_url(url: str) -> tuple[str, str]:  # 新增代码: 下载网页并返回最终 URL 和文本；若省略: search/fetch 都需要重复写请求逻辑
    parsed = urllib.parse.urlparse(url)  # 新增代码: 解析 URL 以检查协议；若省略: file:// 等不该访问的协议可能被误用
    if parsed.scheme not in {"http", "https"}:  # 新增代码: 只允许 http/https；若省略: 工具可能访问本地文件或其他敏感协议
        raise RuntimeError("只支持 http 或 https URL。")  # 新增代码: 给模型和用户明确错误原因；若省略: 协议错误难以排查
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # 新增代码: 构造带 User-Agent 的请求；若省略: 部分网站会拒绝默认请求头
    try:  # 新增代码: 捕获网络请求异常；若省略: DNS/超时/HTTP 错误会直接抛出底层异常
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:  # 新增代码: 发起请求并确保响应自动关闭；若省略: 网络连接句柄可能泄漏
            charset = response.headers.get_content_charset() or "utf-8"  # 新增代码: 尽量按网页声明编码解码；若省略: 中文网页可能乱码
            raw_bytes = response.read(MAX_RAW_BYTES)  # 新增代码: 限制读取字节数；若省略: 大网页可能拖慢或占满内存
            final_url = response.geturl()  # 新增代码: 保存重定向后的最终 URL；若省略: 用户不知道实际读取的是哪个网页
    except urllib.error.URLError as error:  # 新增代码: 捕获标准库网络错误；若省略: 用户会看到晦涩异常类型
        raise RuntimeError(f"网页请求失败：{error}") from error  # 新增代码: 转成可读中文错误；若省略: 排查网络问题更困难
    text = raw_bytes.decode(charset, errors="replace")  # 新增代码: 把字节解码成字符串并容忍坏字符；若省略: 少量乱码可能导致整个工具失败
    return final_url, text  # 新增代码: 返回最终地址和页面文本；若省略: 调用方拿不到下载结果


def extract_text_from_html(html_text: str) -> str:  # 新增代码: 从 HTML 中提取正文；若省略: fetch_url 返回会充满标签
    parser = TextExtractor()  # 新增代码: 创建正文提取器；若省略: 无法解析 HTML
    parser.feed(html_text)  # 新增代码: 把 HTML 输入解析器；若省略: parser 中没有正文片段
    return parser.text()  # 新增代码: 返回清理后的正文；若省略: 调用方拿不到可读文本


def run_web_search(arguments: dict[str, Any]) -> str:  # 新增代码: 执行 web_search 工具主体；若省略: tools/call 无法处理搜索请求
    query = str(arguments.get("query", "")).strip()  # 新增代码: 读取并清理搜索关键词；若省略: 空格或非字符串参数会影响搜索
    if not query:  # 新增代码: 拒绝空搜索词；若省略: 工具可能请求无意义页面
        raise RuntimeError("web_search 需要 query 参数。")  # 新增代码: 返回清晰参数错误；若省略: 用户不知道该补什么
    max_results = clamp_int(arguments.get("max_results"), default=5, minimum=1, maximum=8)  # 新增代码: 限制搜索结果数量；若省略: 过多结果会浪费上下文
    search_url = "https://lite.duckduckgo.com/lite/?" + urllib.parse.urlencode({"q": query})  # 新增代码: 构造 DuckDuckGo Lite 搜索 URL；若省略: 中文查询不能安全进入 URL
    final_url, html_text = fetch_raw_url(search_url)  # 新增代码: 下载搜索结果页；若省略: 无法得到搜索结果 HTML
    parser = LinkCollector()  # 新增代码: 创建链接解析器；若省略: 无法从 HTML 中提取结果链接
    parser.feed(html_text)  # 新增代码: 解析搜索结果 HTML；若省略: parser.links 会保持为空
    seen_urls: set[str] = set()  # 新增代码: 记录已返回 URL，避免重复结果；若省略: 同一链接可能多次出现
    results: list[tuple[str, str]] = []  # 新增代码: 保存去重后的搜索结果；若省略: 无法控制最终结果数量
    for title, url in parser.links:  # 新增代码: 遍历解析出的候选链接；若省略: 搜索结果不会被处理
        if url in seen_urls:  # 新增代码: 跳过重复 URL；若省略: 同一网页可能重复占用结果名额
            continue  # 新增代码: 继续处理下一个候选；若省略: 重复链接仍会进入列表
        seen_urls.add(url)  # 新增代码: 标记 URL 已使用；若省略: 后续无法去重
        results.append((title, url))  # 新增代码: 保存一个可返回结果；若省略: 最终输出为空
        if len(results) >= max_results:  # 新增代码: 达到用户要求数量后停止；若省略: 会继续收集过多结果
            break  # 新增代码: 提前退出循环节省处理；若省略: 无意义地继续遍历所有链接
    if not results:  # 新增代码: 处理没有解析出搜索结果的情况；若省略: 用户会看到空列表但不知道原因
        return f"没有从搜索页解析到结果。搜索页：{final_url}"  # 新增代码: 返回可读提示和搜索页地址；若省略: 排查搜索失败更困难
    lines = [f"搜索关键词：{query}", f"搜索页：{final_url}", "搜索结果："]  # 新增代码: 准备输出头部；若省略: 模型难以知道结果对应哪个查询
    for index, (title, url) in enumerate(results, start=1):  # 新增代码: 给每条结果编号；若省略: 多个结果不易引用
        lines.append(f"{index}. {title}\n   URL: {url}")  # 新增代码: 输出标题和 URL；若省略: 模型无法继续调用 fetch_url 读取具体网页
    return "\n".join(lines)  # 新增代码: 返回多行文本结果；若省略: MCP 调用没有可读输出


def run_fetch_url(arguments: dict[str, Any]) -> str:  # 新增代码: 执行 fetch_url 工具主体；若省略: tools/call 无法读取网页
    url = str(arguments.get("url", "")).strip()  # 新增代码: 读取并清理 URL 参数；若省略: 前后空格会导致请求失败
    if not url:  # 新增代码: 拒绝空 URL；若省略: 工具可能请求无意义地址
        raise RuntimeError("fetch_url 需要 url 参数。")  # 新增代码: 返回清晰参数错误；若省略: 用户不知道该传什么
    max_chars = clamp_int(arguments.get("max_chars"), default=DEFAULT_MAX_CHARS, minimum=500, maximum=12000)  # 新增代码: 限制网页正文返回长度；若省略: 长网页会挤占模型上下文
    final_url, html_text = fetch_raw_url(url)  # 新增代码: 下载目标网页；若省略: 无法读取网页内容
    text = extract_text_from_html(html_text)  # 新增代码: 把 HTML 转成正文文本；若省略: 返回内容不适合模型阅读
    if not text:  # 新增代码: 处理网页没有正文的情况；若省略: 用户只会看到空内容
        text = normalize_spaces(html_text)  # 新增代码: 兜底返回清理后的原始文本；若省略: 空正文页面没有任何反馈
    clipped = text[:max_chars]  # 新增代码: 截断正文到安全长度；若省略: 工具可能返回超长内容
    suffix = "\n\n[内容已截断]" if len(text) > max_chars else ""  # 新增代码: 标记内容是否被截断；若省略: 模型可能误以为看到了完整页面
    return f"最终 URL：{final_url}\n正文：\n{clipped}{suffix}"  # 新增代码: 返回最终地址和正文；若省略: 模型无法引用网页来源


def tool_result(text: str) -> dict[str, Any]:  # 新增代码: 把普通文本包装成 MCP content 结果；若省略: tools/call 返回格式不符合 MCP 习惯
    return {"content": [{"type": "text", "text": text}]}  # 新增代码: 返回标准文本 content；若省略: learning_agent 的 McpStdioClient 难以提取工具结果


def make_response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:  # 新增代码: 构造 JSON-RPC 成功响应；若省略: 每个分支都要重复响应格式
    return {"jsonrpc": "2.0", "id": request_id, "result": result}  # 新增代码: 返回带 id 的成功响应；若省略: MCP client 无法匹配请求和响应


def make_error(request_id: Any, code: int, message: str) -> dict[str, Any]:  # 新增代码: 构造 JSON-RPC 错误响应；若省略: 工具失败时没有标准错误格式
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}  # 新增代码: 返回标准错误对象；若省略: client 不能清楚知道失败原因


def handle_tools_call(params: dict[str, Any]) -> dict[str, Any]:  # 新增代码: 分发 MCP tools/call 请求；若省略: 外部工具只能列出不能执行
    name = str(params.get("name", "")).strip()  # 新增代码: 读取 MCP 原始工具名；若省略: 无法判断用户要调用哪个工具
    arguments = params.get("arguments", {})  # 新增代码: 读取工具参数；若省略: web_search 和 fetch_url 拿不到输入
    if not isinstance(arguments, dict):  # 新增代码: 确保参数是对象；若省略: 工具主体可能在非字典上调用 get 崩溃
        arguments = {}  # 新增代码: 非对象参数兜底为空字典；若省略: 参数错误会更难读
    if name == "web_search":  # 新增代码: 处理搜索工具；若省略: 模型无法搜索网页
        return tool_result(run_web_search(arguments))  # 新增代码: 执行搜索并包装文本结果；若省略: 搜索结果不会返回给 agent
    if name == "fetch_url":  # 新增代码: 处理网页读取工具；若省略: 模型无法打开具体网页
        return tool_result(run_fetch_url(arguments))  # 新增代码: 执行网页读取并包装文本结果；若省略: 网页正文不会返回给 agent
    raise RuntimeError(f"未知工具：{name}")  # 新增代码: 未知工具返回清晰错误；若省略: 拼错工具名时很难排查


def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:  # 新增代码: 处理单条 JSON-RPC 消息；若省略: 主循环无法响应 MCP 请求
    method = str(message.get("method", ""))  # 新增代码: 读取 JSON-RPC 方法名；若省略: 无法分发 initialize/tools/list/tools/call
    request_id = message.get("id")  # 新增代码: 读取请求 id；若省略: 响应无法和请求匹配
    params = message.get("params", {})  # 新增代码: 读取请求参数；若省略: tools/call 无法拿到工具名和参数
    if method == "notifications/initialized":  # 新增代码: 处理 MCP 初始化完成通知；若省略: client 发通知时会收到不必要错误
        return None  # 新增代码: notification 不需要响应；若省略: 会违反通知不带响应的习惯
    if method == "initialize":  # 新增代码: 处理 MCP 初始化握手；若省略: learning_agent 的 McpStdioClient 启动会失败
        return make_response(request_id, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "browser_search", "version": "0.1"}})  # 新增代码: 返回 server 能力和版本；若省略: client 不知道 server 是否支持 tools
    if method == "tools/list":  # 新增代码: 处理工具列表请求；若省略: 模型永远看不到 web_search/fetch_url
        return make_response(request_id, {"tools": TOOLS})  # 新增代码: 返回两个 MCP 工具定义；若省略: learning_agent 没有外部工具 schema
    if method == "tools/call":  # 新增代码: 处理工具调用请求；若省略: 模型选择工具后无法执行
        if not isinstance(params, dict):  # 新增代码: 确认 params 是对象；若省略: 坏请求可能导致属性访问异常
            return make_error(request_id, -32602, "tools/call params 必须是对象。")  # 新增代码: 返回标准参数错误；若省略: 用户看不到清晰失败原因
        try:  # 新增代码: 捕获工具运行时错误并转换成 JSON-RPC 错误；若省略: server 可能直接退出
            return make_response(request_id, handle_tools_call(params))  # 新增代码: 执行工具并返回成功响应；若省略: 工具结果不会回到 client
        except Exception as error:  # 新增代码: 捕获搜索/网页读取异常；若省略: 网络失败会杀死 MCP server
            return make_error(request_id, -32000, str(error))  # 新增代码: 把异常转成可读 MCP 错误；若省略: agent 难以向用户解释失败原因
    return make_error(request_id, -32601, f"未知 MCP 方法：{method}")  # 新增代码: 未知方法返回标准错误；若省略: 协议问题不易排查


def write_message(message: dict[str, Any]) -> None:  # 新增代码: 向 stdout 写出一条 JSON-RPC 响应；若省略: 主循环需要重复写序列化逻辑
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")  # 新增代码: 写单行 JSON 并保留中文；若省略: client 的 readline 无法读取完整响应
    sys.stdout.flush()  # 新增代码: 立即刷新 stdout；若省略: 响应可能停在缓冲区导致 client 超时


def run_server() -> None:  # 新增代码: 运行 stdio MCP server 主循环；若省略: 这个脚本被启动后不会处理任何请求
    for raw_line in sys.stdin:  # 新增代码: 持续读取 client 发来的每一行 JSON-RPC；若省略: server 无法接收请求
        raw_line = raw_line.strip()  # 新增代码: 去掉换行和边缘空白；若省略: json.loads 仍可处理但日志和判断不整洁
        if not raw_line:  # 新增代码: 跳过空行；若省略: 空输入会产生 JSON 解析错误
            continue  # 新增代码: 继续等待下一条消息；若省略: 空行会进入解析流程
        try:  # 新增代码: 捕获单条消息解析和处理错误；若省略: 一条坏消息会让 server 退出
            message = json.loads(raw_line)  # 新增代码: 解析 JSON-RPC 消息；若省略: server 无法理解 client 请求
            response = handle_message(message if isinstance(message, dict) else {})  # 新增代码: 只处理对象消息；若省略: 非对象 JSON 可能导致属性错误
        except Exception as error:  # 新增代码: 捕获解析或处理异常；若省略: server 可能因坏输入崩溃
            response = make_error(None, -32700, f"JSON-RPC 消息处理失败：{error}")  # 新增代码: 返回可读解析错误；若省略: client 只能看到 stdout 关闭
        if response is not None:  # 新增代码: notification 没有响应，普通请求才写回；若省略: initialized 通知也会收到响应
            write_message(response)  # 新增代码: 把响应写给 MCP client；若省略: client 会一直等待直到超时


if __name__ == "__main__":  # 新增代码: 仅在脚本直接运行时启动 MCP server；若省略: 导入测试时也会阻塞读取 stdin
    run_server()  # 新增代码: 启动 stdio MCP 主循环；若省略: 作为 MCP server 启动后不会工作
