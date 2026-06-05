import re  # 修改代码+DesktopTaskRouter：导入正则模块用于英文词边界匹配；如果没有这一行，test/contest、app/happy、paint/painting 仍会被裸子串误判。
from dataclasses import dataclass  # 新增代码+DesktopTaskRouter：导入 dataclass 来定义轻量意图结果对象；如果没有这一行，分类结果就需要手写大量样板代码，项目更难读懂。
from typing import Dict, Iterable, Tuple  # 修改代码+DesktopTaskRouter：导入类型标注用的容器类型；如果没有这一行，函数输入输出结构就不够清楚，后续维护更容易误用。


_FALSE_POSITIVE_CHINESE_KEYWORDS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义中文开发/文档/git/测试类误报保护关键词；如果没有这一组，普通中文代码任务可能被错误送去控制本地桌面。
    "函数",  # 修改代码+DesktopTaskRouter：保护中文函数解释请求；如果没有这一项，函数报错问题可能被误认为需要操作本地电脑。
    "代码",  # 修改代码+DesktopTaskRouter：保护代码解释和代码修改请求；如果没有这一项，提到画图代码时可能误进桌面路线。
    "报错",  # 修改代码+DesktopTaskRouter：保护报错解释请求；如果没有这一项，调试问题可能被误判成 GUI 操作。
    "错误",  # 修改代码+DesktopTaskRouter：保护错误分析请求；如果没有这一项，错误说明可能触发桌面任务路由。
    "解释",  # 修改代码+DesktopTaskRouter：保护解释型请求；如果没有这一项，用户让解释 Paint/代码时可能被当成执行操作。
    "修改代码",  # 修改代码+DesktopTaskRouter：保护中文代码修改请求；如果没有这一项，代码编辑任务可能被错送本地应用路线。
    "代码修改",  # 修改代码+DesktopTaskRouter：保护另一种中文代码修改说法；如果没有这一项，等价表述会漏过误报保护。
    "文档",  # 修改代码+DesktopTaskRouter：保护文档请求；如果没有这一项，README 或说明文字任务可能被误判为桌面操作。
    "测试",  # 修改代码+DesktopTaskRouter：保护中文测试请求；如果没有这一项，运行测试的 prompt 可能误进 GUI 路线。
    "单元测试",  # 修改代码+DesktopTaskRouter：保护中文单元测试请求；如果没有这一项，单测任务可能被当成本地应用任务。
)  # 修改代码+DesktopTaskRouter：结束中文误报保护关键词元组；如果没有这一行，Python 语法结构就不完整。

_FALSE_POSITIVE_ENGLISH_TERMS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义英文开发/文档/git/测试类误报保护词或短语；如果没有这一组，英文代码任务可能被错误送去控制本地桌面。
    "python",  # 修改代码+DesktopTaskRouter：保护 Python 问题不被误判为桌面任务；如果没有这一项，用户问 Python 函数报错可能误进 GUI 路线。
    "readme",  # 修改代码+DesktopTaskRouter：保护 README 请求；如果没有这一项，提到画图说明的 README 修改可能误进桌面路线。
    "git",  # 修改代码+DesktopTaskRouter：保护 git 请求；如果没有这一项，commit/branch 类 prompt 可能被 desktop 关键词误导。
    "commit",  # 修改代码+DesktopTaskRouter：保护提交请求；如果没有这一项，用户要求提交代码可能被误判为桌面任务。
    "test",  # 修改代码+DesktopTaskRouter：按词边界保护英文测试请求；如果没有这一项，unit test 会漏过误报保护。
    "unit test",  # 修改代码+DesktopTaskRouter：保护英文单元测试短语；如果没有这一项，单元测试场景的保护不够直观。
    "docs",  # 修改代码+DesktopTaskRouter：保护英文文档请求；如果没有这一项，文档类任务可能因为 desktop/paint 误报。
    "documentation",  # 修改代码+DesktopTaskRouter：保护英文文档说明请求；如果没有这一项，长写法会漏过误报保护。
    "explain",  # 修改代码+DesktopTaskRouter：保护英文解释型请求；如果没有这一项，how/explain 类问题可能误进执行路线。
    "modify code",  # 修改代码+DesktopTaskRouter：保护英文代码修改请求；如果没有这一项，代码变更请求可能被误送 GUI。
    "code",  # 修改代码+DesktopTaskRouter：保护英文代码问题；如果没有这一项，paint code 这类文字会触发误报。
)  # 修改代码+DesktopTaskRouter：结束英文误报保护词元组；如果没有这一行，Python 语法结构就不完整。

_LOCAL_CONTEXT_CHINESE_KEYWORDS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义中文本地电脑/桌面上下文关键词；如果没有这一组，分类器无法区分本地 GUI 任务和普通聊天请求。
    "本地电脑",  # 修改代码+DesktopTaskRouter：识别用户明确说本地电脑；如果没有这一项，核心中文验收 prompt 会漏判。
    "本机",  # 修改代码+DesktopTaskRouter：识别“本机”说法；如果没有这一项，常见中文本地表达会漏判。
    "本地应用",  # 修改代码+DesktopTaskRouter：识别本地应用请求；如果没有这一项，泛化 local-app 场景会变弱。
    "本地软件",  # 修改代码+DesktopTaskRouter：识别本地软件请求；如果没有这一项，中文软件场景可能漏判。
    "电脑",  # 修改代码+DesktopTaskRouter：识别电脑上下文；如果没有这一项，中文桌面任务的本地信号会少一类。
    "桌面",  # 修改代码+DesktopTaskRouter：识别桌面上下文；如果没有这一项，中文桌面任务可能漏判。
)  # 修改代码+DesktopTaskRouter：结束中文本地上下文关键词元组；如果没有这一行，Python 语法结构就不完整。

_LOCAL_CONTEXT_ENGLISH_TERMS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义英文本地电脑/桌面上下文词或短语；如果没有这一组，英文 local GUI 请求会漏判。
    "windows",  # 修改代码+DesktopTaskRouter：识别 Windows 本地环境；如果没有这一项，英文/混合 Windows prompt 可能漏判。
    "desktop",  # 修改代码+DesktopTaskRouter：识别英文桌面上下文；如果没有这一项，英文 desktop prompt 会漏判。
    "computer",  # 修改代码+DesktopTaskRouter：识别英文电脑上下文；如果没有这一项，英文 computer prompt 会漏判。
    "local app",  # 修改代码+DesktopTaskRouter：识别英文 local app；如果没有这一项，英文泛化本地应用请求会漏判。
    "local application",  # 修改代码+DesktopTaskRouter：识别英文 local application；如果没有这一项，正式写法会漏判。
    "local computer",  # 修改代码+DesktopTaskRouter：识别英文 local computer；如果没有这一项，英文明确本地电脑请求会漏判。
    "on this pc",  # 修改代码+DesktopTaskRouter：识别“这台 PC”说法；如果没有这一项，常见英文表达会漏判。
    "on my pc",  # 修改代码+DesktopTaskRouter：识别“我的 PC”说法；如果没有这一项，个人电脑表达会漏判。
    "on my computer",  # 修改代码+DesktopTaskRouter：识别“我的电脑”英文说法；如果没有这一项，英文自然表达会漏判。
)  # 修改代码+DesktopTaskRouter：结束英文本地上下文词元组；如果没有这一行，Python 语法结构就不完整。

_GUI_OPERATION_CHINESE_KEYWORDS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义中文明确 GUI 操作动词且不包含单字“画”；如果没有这一组，中文 GUI 操作无法与知识性画图问题区分。
    "打开",  # 修改代码+DesktopTaskRouter：识别中文打开应用动作；如果没有这一项，打开画图这类请求会漏判。
    "使用",  # 修改代码+DesktopTaskRouter：识别中文使用应用动作；如果没有这一项，核心中文验收 prompt 会漏判。
    "控制",  # 修改代码+DesktopTaskRouter：识别中文控制动作；如果没有这一项，控制本地应用的请求会漏判。
    "操作",  # 修改代码+DesktopTaskRouter：识别中文操作动作；如果没有这一项，泛化 GUI 操作请求会漏判。
    "启动",  # 修改代码+DesktopTaskRouter：识别中文启动动作；如果没有这一项，启动本地软件请求会漏判。
    "运行",  # 修改代码+DesktopTaskRouter：识别中文运行动作；如果没有这一项，运行本地程序请求会漏判。
    "点击",  # 修改代码+DesktopTaskRouter：识别中文点击动作；如果没有这一项，鼠标操作请求会漏判。
    "输入",  # 修改代码+DesktopTaskRouter：识别中文输入动作；如果没有这一项，键盘输入任务会漏判。
    "拖动",  # 修改代码+DesktopTaskRouter：识别中文拖动动作；如果没有这一项，拖拽类 GUI 任务会漏判。
)  # 修改代码+DesktopTaskRouter：结束中文 GUI 操作关键词元组；如果没有这一行，Python 语法结构就不完整。

_GUI_OPERATION_ENGLISH_TERMS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义英文明确 GUI 操作词且按词边界匹配；如果没有这一组，英文打开/使用/控制应用请求会漏判。
    "open",  # 修改代码+DesktopTaskRouter：识别英文打开动作；如果没有这一项，open Paint 会漏判。
    "use",  # 修改代码+DesktopTaskRouter：识别英文使用动作；如果没有这一项，Use mspaint 会漏判。
    "control",  # 修改代码+DesktopTaskRouter：识别英文控制动作；如果没有这一项，control local app 会漏判。
    "operate",  # 修改代码+DesktopTaskRouter：识别英文操作动作；如果没有这一项，operate app 的说法会漏判。
    "launch",  # 修改代码+DesktopTaskRouter：识别英文启动动作；如果没有这一项，launch mspaint 会漏判。
    "start",  # 修改代码+DesktopTaskRouter：识别英文启动动作；如果没有这一项，start Paint 会漏判。
    "click",  # 修改代码+DesktopTaskRouter：识别英文点击动作；如果没有这一项，点击类 GUI 请求会漏判。
    "type",  # 修改代码+DesktopTaskRouter：识别英文输入动作；如果没有这一项，键盘输入请求会漏判。
    "drag",  # 修改代码+DesktopTaskRouter：识别英文拖动动作；如果没有这一项，拖拽类 GUI 请求会漏判。
)  # 修改代码+DesktopTaskRouter：结束英文 GUI 操作词元组；如果没有这一行，Python 语法结构就不完整。

_ENGLISH_OPEN_LOCAL_TERMS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义可推断“打开本地应用”的英文动作词；如果没有这一组，Contest Manager 这类无 app 单词的本地打开请求会被漏判或误拒。
    "open",  # 修改代码+DesktopTaskRouter：允许 Open Contest Manager on my computer 识别为本地 GUI 请求；如果没有这一项，审查里的 Contest 正例无法保留。
    "launch",  # 修改代码+DesktopTaskRouter：允许 launch 某应用的英文请求进入泛化本地 GUI 判断；如果没有这一项，常见启动说法会漏判。
    "use",  # 修改代码+DesktopTaskRouter：允许 use 某应用的英文请求进入泛化本地 GUI 判断；如果没有这一项，使用本地应用的说法会漏判。
    "control",  # 修改代码+DesktopTaskRouter：允许 control 某应用的英文请求进入泛化本地 GUI 判断；如果没有这一项，控制本地应用的说法会漏判。
)  # 修改代码+DesktopTaskRouter：结束英文打开本地应用动作词元组；如果没有这一行，Python 语法结构就不完整。

_DRAWING_CHINESE_KEYWORDS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义中文明确绘制目标短语而不是单字“画”；如果没有这一组，画一个皮卡丘这类目标无法与画图技巧类知识问题区分。
    "画一个",  # 修改代码+DesktopTaskRouter：识别“画一个”目标；如果没有这一项，核心中文绘图请求可能漏判。
    "画一只",  # 修改代码+DesktopTaskRouter：识别“画一只”目标；如果没有这一项，动物绘制请求可能漏判。
    "画个",  # 修改代码+DesktopTaskRouter：识别口语“画个”目标；如果没有这一项，口语绘图请求可能漏判。
    "画出",  # 修改代码+DesktopTaskRouter：识别“画出”目标；如果没有这一项，明确绘制结果的请求可能漏判。
    "绘制",  # 修改代码+DesktopTaskRouter：识别中文绘制正式说法；如果没有这一项，正式绘图 prompt 会漏判。
)  # 修改代码+DesktopTaskRouter：结束中文绘制目标短语元组；如果没有这一行，Python 语法结构就不完整。

_DRAWING_ENGLISH_TERMS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义英文绘制动作词且按词边界匹配；如果没有这一组，draw in Paint 这类请求会漏判。
    "draw",  # 修改代码+DesktopTaskRouter：识别英文绘图动作；如果没有这一项，draw with Paint 会漏判。
)  # 修改代码+DesktopTaskRouter：结束英文绘制动作词元组；如果没有这一行，Python 语法结构就不完整。

_GENERIC_APP_CHINESE_KEYWORDS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义中文泛化本地应用关键词；如果没有这一组，分类器只能识别 Paint，不能覆盖 local-app 基础组合。
    "软件",  # 修改代码+DesktopTaskRouter：识别中文软件；如果没有这一项，泛化本地软件请求会漏判。
    "应用",  # 修改代码+DesktopTaskRouter：识别中文应用；如果没有这一项，泛化本地应用请求会漏判。
    "程序",  # 修改代码+DesktopTaskRouter：识别中文程序；如果没有这一项，启动程序类请求会漏判。
)  # 修改代码+DesktopTaskRouter：结束中文泛化应用关键词元组；如果没有这一行，Python 语法结构就不完整。

_GENERIC_APP_ENGLISH_TERMS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义英文泛化应用词并按词边界匹配；如果没有这一组，app 会继续命中 happy 这样的普通单词。
    "app",  # 修改代码+DesktopTaskRouter：识别独立英文 app 单词；如果没有这一项，local app 请求会漏判。
    "application",  # 修改代码+DesktopTaskRouter：识别英文 application；如果没有这一项，正式英文应用请求会漏判。
    "program",  # 修改代码+DesktopTaskRouter：识别英文 program；如果没有这一项，程序类桌面任务会漏判。
)  # 修改代码+DesktopTaskRouter：结束英文泛化应用词元组；如果没有这一行，Python 语法结构就不完整。

_CHINESE_PAINT_APP_KEYWORDS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义中文 Paint/画图应用关键词；如果没有这一组，中文画图软件请求无法稳定识别目标应用。
    "画图软件",  # 修改代码+DesktopTaskRouter：识别核心中文“画图软件”；如果没有这一项，用户指定 Paint 类应用时可能漏判。
    "画图应用",  # 修改代码+DesktopTaskRouter：识别中文“画图应用”；如果没有这一项，同义表达会漏判。
    "画图程序",  # 修改代码+DesktopTaskRouter：识别中文“画图程序”；如果没有这一项，程序说法会漏判。
    "微软画图",  # 修改代码+DesktopTaskRouter：识别 Microsoft Paint 中文名；如果没有这一项，明确目标应用会漏判。
    "windows画图",  # 修改代码+DesktopTaskRouter：识别不带空格的 Windows 画图；如果没有这一项，紧凑写法会漏判。
    "windows 画图",  # 修改代码+DesktopTaskRouter：识别带空格的 Windows 画图；如果没有这一项，混合写法会漏判。
    "画图",  # 修改代码+DesktopTaskRouter：识别简短画图应用说法；如果没有这一项，“打开画图”这类自然请求会漏判。
)  # 修改代码+DesktopTaskRouter：结束中文画图关键词元组；如果没有这一行，Python 语法结构就不完整。

_ENGLISH_PAINT_APP_TERMS: Tuple[str, ...] = (  # 修改代码+DesktopTaskRouter：定义英文 Paint 应用词并按词边界匹配；如果没有这一组，paint 会继续命中 painting。
    "mspaint",  # 修改代码+DesktopTaskRouter：识别 Windows 画图可执行程序名；如果没有这一项，最明确的 mspaint 请求会漏判。
    "paint",  # 修改代码+DesktopTaskRouter：识别独立英文 Paint 应用名；如果没有这一项，open Paint/draw in Paint 会漏判。
    "microsoft paint",  # 修改代码+DesktopTaskRouter：识别 Microsoft Paint 全称；如果没有这一项，正式英文应用名会漏判。
)  # 修改代码+DesktopTaskRouter：结束英文 Paint 应用词元组；如果没有这一行，Python 语法结构就不完整。


# 新增代码+DesktopTaskRouter：类段开始，DesktopTaskIntent 用来承载脱敏后的桌面任务分类结果；如果没有这个类，后续 Task 3+ 无法用稳定字段判断是否需要 GUI 路线，作者意图是让路由输出结构清楚并且不保存原始 prompt，本类会与 classify_desktop_task 配合使用，类段到字段和方法定义结束为止。
@dataclass(frozen=True)  # 新增代码+DesktopTaskRouter：让意图结果不可变且自动生成初始化逻辑；如果没有这一行，调用方可能不小心改写分类结果，造成后续路由判断不稳定。
class DesktopTaskIntent:  # 新增代码+DesktopTaskRouter：定义桌面任务意图结果类；如果没有这一行，项目没有 Task 2 要求的 DesktopTaskIntent 输出类型。
    is_desktop_task: bool  # 新增代码+DesktopTaskRouter：记录是否应该进入桌面任务路线；如果没有这一字段，后续无法做最核心的路由分流。
    reason: str  # 新增代码+DesktopTaskRouter：记录脱敏后的分类原因码；如果没有这一字段，测试和日志无法解释为什么判定或拒绝。
    target_app_hint: str  # 新增代码+DesktopTaskRouter：记录目标应用提示，例如画图或 mspaint；如果没有这一字段，后续运行层不知道该优先处理哪个本地应用。
    task_goal: str  # 新增代码+DesktopTaskRouter：记录短的类型化目标摘要；如果没有这一字段，后续只能保存原始 prompt 才能表达目标，会增加隐私风险。
    requires_gui_actions: bool  # 新增代码+DesktopTaskRouter：记录任务是否需要 GUI 动作；如果没有这一字段，脚本路线和真实 GUI 路线不容易区分。
    raw_prompt_included: bool = False  # 新增代码+DesktopTaskRouter：明确标记结构化结果不包含用户原始 prompt；如果没有这一字段，调用方无法确认路由结果是否脱敏。

    def to_dict(self) -> Dict[str, object]:  # 新增代码+DesktopTaskRouter：函数段开始，把意图结果转成公开字典；如果没有这个函数，调用方可能直接打印对象并误以为包含完整上下文，作者意图是提供稳定、脱敏、可测试的公开摘要，本函数与测试中的 raw prompt 泄漏检查配合使用，函数段到 return 结束为止。
        return {  # 新增代码+DesktopTaskRouter：返回只含稳定字段的字典；如果没有这一行，调用方就拿不到可序列化结果。
            "is_desktop_task": self.is_desktop_task,  # 新增代码+DesktopTaskRouter：公开是否桌面任务；如果没有这一项，字典消费者无法做路由判断。
            "reason": self.reason,  # 新增代码+DesktopTaskRouter：公开脱敏原因码；如果没有这一项，调试时不知道为什么分类。
            "target_app_hint": self.target_app_hint,  # 新增代码+DesktopTaskRouter：公开目标应用提示；如果没有这一项，运行层无法获得应用线索。
            "task_goal": self.task_goal,  # 新增代码+DesktopTaskRouter：公开短目标摘要；如果没有这一项，后续阶段缺少脱敏任务目标。
            "requires_gui_actions": self.requires_gui_actions,  # 新增代码+DesktopTaskRouter：公开是否需要 GUI 动作；如果没有这一项，策略层无法阻止脚本绕路。
            "raw_prompt_included": self.raw_prompt_included,  # 新增代码+DesktopTaskRouter：公开原始 prompt 未保存标记；如果没有这一项，调用方无法检查隐私边界。
        }  # 新增代码+DesktopTaskRouter：结束公开字典构造；如果没有这一行，Python 字典语法不完整。

    def __str__(self) -> str:  # 新增代码+DesktopTaskRouter：函数段开始，提供不含原始 prompt 的字符串摘要；如果没有这个函数，默认 repr 仍不含 prompt 但格式不够明确，作者意图是让人工查看时也只看到脱敏字段，本函数与 to_dict 一起保护公开摘要，函数段到 return 结束为止。
        return f"DesktopTaskIntent({self.to_dict()})"  # 新增代码+DesktopTaskRouter：用公开字典生成字符串；如果没有这一行，调试输出可能不稳定也不方便测试脱敏边界。


def _normalize_prompt(prompt: str) -> str:  # 新增代码+DesktopTaskRouter：函数段开始，把输入 prompt 规范成小写字符串；如果没有这个函数，大小写和空白会让关键词匹配不稳定，作者意图是给 classify_desktop_task 提供统一输入，本函数段到 return 结束为止。
    if not isinstance(prompt, str):  # 新增代码+DesktopTaskRouter：先确认输入是字符串；如果没有这一行，调用方传 None 或列表时 strip 会抛异常。
        return ""  # 新增代码+DesktopTaskRouter：非字符串输入按空 prompt 处理；如果没有这一行，坏输入会中断整个分类流程。
    return prompt.strip().lower()  # 新增代码+DesktopTaskRouter：去掉首尾空白并转小写；如果没有这一行，关键词匹配会受大小写和空格影响。


def _contains_any(text: str, keywords: Iterable[str]) -> bool:  # 修改代码+DesktopTaskRouter：函数段开始，只给中文短语做包含匹配；如果没有这个函数，多处中文匹配逻辑会重复且更容易写错，作者意图是把中文和英文边界匹配分开，本函数段到 return 结束为止。
    return any(keyword in text for keyword in keywords)  # 修改代码+DesktopTaskRouter：只要命中任一中文短语就返回 True；如果没有这一行，分类器无法判断中文关键词组合。


def _english_term_to_pattern(term: str) -> str:  # 修改代码+DesktopTaskRouter：函数段开始，把英文词或短语转成允许空白变化的正则片段；如果没有这个函数，短语如 unit test/local computer 不方便安全匹配，作者意图是支撑统一词边界检查，本函数段到 return 结束为止。
    return r"\s+".join(re.escape(part) for part in term.split())  # 修改代码+DesktopTaskRouter：逐词转义并用空白连接；如果没有这一行，短语匹配会受空格数量影响或出现正则注入风险。


def _contains_english_term(text: str, terms: Iterable[str]) -> bool:  # 修改代码+DesktopTaskRouter：函数段开始，按英文词/短语边界检查是否命中；如果没有这个函数，test 会命中 contest、app 会命中 happy、paint 会命中 painting，作者意图是治本收紧英文匹配，本函数段到循环和 return 结束为止。
    for term in terms:  # 修改代码+DesktopTaskRouter：逐个检查英文词或短语；如果没有这一行，无法对每个候选词生成独立边界正则。
        pattern = rf"(?<![a-z0-9_]){_english_term_to_pattern(term)}(?![a-z0-9_])"  # 修改代码+DesktopTaskRouter：构造英文左右边界正则；如果没有这一行，子串误命中问题无法根治。
        if re.search(pattern, text):  # 修改代码+DesktopTaskRouter：用正则检查当前词或短语是否命中；如果没有这一行，匹配结果不会被实际计算。
            return True  # 修改代码+DesktopTaskRouter：命中任一英文词或短语就返回 True；如果没有这一行，已命中的关键词仍会被忽略。
    return False  # 修改代码+DesktopTaskRouter：所有英文词或短语都没命中时返回 False；如果没有这一行，调用方会拿到 None 导致布尔逻辑不清晰。


def _contains_development_keyword(text: str) -> bool:  # 修改代码+DesktopTaskRouter：函数段开始，统一判断开发/文档/git/测试误报保护；如果没有这个函数，误报保护会继续混用中文子串和英文裸子串，作者意图是让英文保护走词边界，本函数段到 return 结束为止。
    return _contains_any(text, _FALSE_POSITIVE_CHINESE_KEYWORDS) or _contains_english_term(text, _FALSE_POSITIVE_ENGLISH_TERMS)  # 修改代码+DesktopTaskRouter：中文用短语包含、英文用词边界；如果没有这一行，contest 仍会被 test 子串误拒。


def _has_local_context(text: str) -> bool:  # 修改代码+DesktopTaskRouter：函数段开始，统一判断本地电脑/桌面上下文；如果没有这个函数，中英文上下文匹配会重复且英文可能再次裸子串误判，作者意图是复用安全边界匹配，本函数段到 return 结束为止。
    return _contains_any(text, _LOCAL_CONTEXT_CHINESE_KEYWORDS) or _contains_english_term(text, _LOCAL_CONTEXT_ENGLISH_TERMS)  # 修改代码+DesktopTaskRouter：中文用短语包含、英文用词边界；如果没有这一行，英文 computer/local app 上下文无法安全识别。


def _has_generic_app_word(text: str) -> bool:  # 修改代码+DesktopTaskRouter：函数段开始，统一判断泛化应用词；如果没有这个函数，英文 app 会继续命中 happy，作者意图是只让独立 app/application/program 生效，本函数段到 return 结束为止。
    return _contains_any(text, _GENERIC_APP_CHINESE_KEYWORDS) or _contains_english_term(text, _GENERIC_APP_ENGLISH_TERMS)  # 修改代码+DesktopTaskRouter：中文用短语包含、英文用词边界；如果没有这一行，happy 里的 app 会继续误触发泛化本地应用。


def _detect_target_app_hint(text: str) -> str:  # 修改代码+DesktopTaskRouter：函数段开始，从脱敏文本中提取目标应用提示；如果没有这个函数，Paint/mspaint 目标无法稳定表达，作者意图是为后续运行层提供短应用线索且避免 painting 子串误判，本函数段到所有 return 结束为止。
    if _contains_english_term(text, ("mspaint",)):  # 修改代码+DesktopTaskRouter：按词边界优先识别最明确的 Windows 画图程序名；如果没有这一行，mspaint 会被泛化成 Paint，精确信号会丢失。
        return "mspaint"  # 新增代码+DesktopTaskRouter：返回稳定 mspaint 提示；如果没有这一行，英文 mspaint 测试无法获得明确目标。
    if _contains_any(text, _CHINESE_PAINT_APP_KEYWORDS):  # 修改代码+DesktopTaskRouter：识别中文画图应用说法；如果没有这一行，中文画图软件请求会漏掉目标应用。
        return "画图"  # 新增代码+DesktopTaskRouter：返回稳定中文画图提示；如果没有这一行，中文测试无法得到稳定 target_app_hint。
    if _contains_english_term(text, _ENGLISH_PAINT_APP_TERMS):  # 修改代码+DesktopTaskRouter：按词边界识别英文 Paint 应用说法；如果没有这一行，painting 会继续被误当成 Paint 应用。
        return "Paint"  # 新增代码+DesktopTaskRouter：返回稳定英文 Paint 提示；如果没有这一行，英文 Paint 场景无法表达目标应用。
    return ""  # 新增代码+DesktopTaskRouter：没有识别到明确应用时返回空提示；如果没有这一行，调用方会拿到 None 并增加额外判空复杂度。


def _has_chinese_paint_gui_action(text: str) -> bool:  # 修改代码+DesktopTaskRouter：函数段开始，判断中文 Paint 请求是否包含明确 GUI 操作；如果没有这个函数，画图是什么软件这类知识问题会继续被“画”误触发，作者意图是只接受打开/使用/在画图中绘制等真实操作表达，本函数段到 return 结束为止。
    has_paint_app = _contains_any(text, _CHINESE_PAINT_APP_KEYWORDS)  # 修改代码+DesktopTaskRouter：先确认中文文本确实提到画图应用；如果没有这一行，普通绘画请求可能被误当成 Paint 应用任务。
    has_operation = _contains_any(text, _GUI_OPERATION_CHINESE_KEYWORDS)  # 修改代码+DesktopTaskRouter：检查打开/使用/控制等明确 GUI 操作；如果没有这一行，无法区分操作请求和介绍请求。
    has_draw_goal = _contains_any(text, _DRAWING_CHINESE_KEYWORDS)  # 修改代码+DesktopTaskRouter：检查画一个/绘制等明确绘制目标；如果没有这一行，核心“画一个皮卡丘”目标会漏判。
    return has_paint_app and (has_operation or (("在画图" in text or "用画图" in text) and has_draw_goal))  # 修改代码+DesktopTaskRouter：画图应用必须配合明确操作或“在/用画图+绘制目标”；如果没有这一行，中文 Paint 正负例无法稳定分开。


def _has_english_paint_gui_action(text: str, has_local_context: bool) -> bool:  # 修改代码+DesktopTaskRouter：函数段开始，判断英文 Paint 请求是否包含明确 GUI 操作；如果没有这个函数，painting 会继续因 paint 子串误触发，作者意图是要求 Paint 应用词边界和 open/use/draw 等明确动作配合，本函数段到 return 结束为止。
    has_paint_app = _contains_english_term(text, _ENGLISH_PAINT_APP_TERMS)  # 修改代码+DesktopTaskRouter：按词边界确认英文 Paint 应用；如果没有这一行，painting 会被误当成 Paint。
    has_operation = _contains_english_term(text, _GUI_OPERATION_ENGLISH_TERMS)  # 修改代码+DesktopTaskRouter：按词边界检查 open/use/control 等 GUI 操作；如果没有这一行，英文 Paint 打开/使用请求会漏判。
    has_draw_goal = _contains_english_term(text, _DRAWING_ENGLISH_TERMS)  # 修改代码+DesktopTaskRouter：按词边界检查 draw 绘制目标；如果没有这一行，draw in Paint 这类请求会漏判。
    return has_paint_app and (has_operation or (has_local_context and has_draw_goal))  # 修改代码+DesktopTaskRouter：Paint 应用必须配合操作词，或在本地上下文中配合 draw；如果没有这一行，英文 Paint 正负例无法稳定分开。


def _has_paint_gui_action(text: str, target_app_hint: str, has_local_context: bool) -> bool:  # 修改代码+DesktopTaskRouter：函数段开始，统一判断 Paint/画图任务是否具有真实 GUI 操作意图；如果没有这个函数，中英文 Paint 判断会散落在主函数里，作者意图是集中处理应用名和动作歧义，本函数段到 return 结束为止。
    if target_app_hint == "画图":  # 修改代码+DesktopTaskRouter：中文画图应用走中文动作规则；如果没有这一行，中文和英文边界规则会混在一起。
        return _has_chinese_paint_gui_action(text)  # 修改代码+DesktopTaskRouter：返回中文 Paint GUI 动作判断；如果没有这一行，中文 Paint 正向请求无法命中。
    if target_app_hint in ("Paint", "mspaint"):  # 修改代码+DesktopTaskRouter：英文 Paint/mspaint 走英文动作规则；如果没有这一行，英文 Paint 正向请求无法命中。
        return _has_english_paint_gui_action(text, has_local_context)  # 修改代码+DesktopTaskRouter：返回英文 Paint GUI 动作判断；如果没有这一行，英文 Paint 负例无法按词边界过滤。
    return False  # 修改代码+DesktopTaskRouter：没有 Paint 目标时返回 False；如果没有这一行，非 Paint 任务可能误走 Paint 规则。


def _looks_like_english_open_local_request(text: str, has_local_context: bool) -> bool:  # 修改代码+DesktopTaskRouter：函数段开始，识别 Open Contest Manager on my computer 这类没有 app 单词但明显打开本地应用的英文请求；如果没有这个函数，Contest 会不被 test 误拒但也难以作为本地 GUI 请求保留，作者意图是窄化支持 open/launch/use/control + 本地上下文，本函数段到 return 结束为止。
    if not has_local_context:  # 修改代码+DesktopTaskRouter：没有本地上下文就不推断本地应用请求；如果没有这一行，普通 open 内容请求可能误入桌面路线。
        return False  # 修改代码+DesktopTaskRouter：缺少本地上下文时保守拒绝；如果没有这一行，误路由风险会变高。
    action_pattern = r"(?<![a-z0-9_])(?:open|launch|use|control)\s+[a-z0-9][a-z0-9\s_-]{1,80}"  # 修改代码+DesktopTaskRouter：只匹配 open/launch/use/control 后面跟目标名称；如果没有这一行，start a timer 这类句子可能被泛化误判。
    return re.search(action_pattern, text) is not None  # 修改代码+DesktopTaskRouter：命中窄化英文打开本地目标模式才返回 True；如果没有这一行，Contest Manager 场景无法摆脱 test 子串误拒后的路由空白。


def _has_generic_gui_action(text: str, has_local_context: bool) -> bool:  # 修改代码+DesktopTaskRouter：函数段开始，判断非 Paint 的泛化本地 GUI 请求；如果没有这个函数，泛化 app 匹配会继续使用裸子串并误判 happy，作者意图是要求本地上下文加明确操作加应用词或窄化 open 目标，本函数段到 return 结束为止。
    has_operation = _contains_any(text, _GUI_OPERATION_CHINESE_KEYWORDS) or _contains_english_term(text, _GUI_OPERATION_ENGLISH_TERMS)  # 修改代码+DesktopTaskRouter：检查中英文明确 GUI 操作；如果没有这一行，泛化任务无法知道用户是否要执行动作。
    has_generic_app_word = _has_generic_app_word(text)  # 修改代码+DesktopTaskRouter：检查中英文应用词且英文按词边界；如果没有这一行，happy/app 子串问题会继续存在。
    has_open_local_target = _looks_like_english_open_local_request(text, has_local_context)  # 修改代码+DesktopTaskRouter：检查英文 open/launch/use/control + 本地上下文的窄化目标模式；如果没有这一行，Contest Manager 审查场景无法合理支持。
    return has_local_context and ((has_operation and has_generic_app_word) or has_open_local_target)  # 修改代码+DesktopTaskRouter：泛化桌面任务必须有本地上下文并满足应用词组合或窄化 open 目标；如果没有这一行，普通电脑相关句子会被误判。


def _task_goal_for(target_app_hint: str, has_gui_action: bool) -> str:  # 新增代码+DesktopTaskRouter：函数段开始，生成不含原始 prompt 的短目标摘要；如果没有这个函数，分类器可能被迫保存用户原话，作者意图是给后续阶段一个脱敏目标码，本函数段到所有 return 结束为止。
    if target_app_hint in ("画图", "Paint", "mspaint") and has_gui_action:  # 新增代码+DesktopTaskRouter：识别 Paint 绘图类目标；如果没有这一行，核心画图任务只能得到泛化目标。
        return "draw_with_local_paint"  # 新增代码+DesktopTaskRouter：返回稳定脱敏目标码；如果没有这一行，测试和后续策略无法稳定识别 Paint 绘图任务。
    return "desktop_gui_task"  # 新增代码+DesktopTaskRouter：其他本地 GUI 任务使用泛化目标码；如果没有这一行，泛化任务没有可用摘要。


def _negative_intent(reason: str, target_app_hint: str = "") -> DesktopTaskIntent:  # 新增代码+DesktopTaskRouter：函数段开始，创建统一的非桌面任务结果；如果没有这个函数，拒绝分支会重复字段且容易忘记 raw_prompt_included=False，作者意图是集中保证脱敏字段一致，本函数段到 return 结束为止。
    return DesktopTaskIntent(  # 新增代码+DesktopTaskRouter：返回非桌面任务意图对象；如果没有这一行，拒绝分支无法生成 Task 2 要求的结构化结果。
        is_desktop_task=False,  # 新增代码+DesktopTaskRouter：明确不是桌面任务；如果没有这一项，调用方无法阻止误路由。
        reason=reason,  # 新增代码+DesktopTaskRouter：写入脱敏拒绝原因；如果没有这一项，调试时不知道拒绝原因。
        target_app_hint=target_app_hint,  # 新增代码+DesktopTaskRouter：保留已识别但未路由的应用提示；如果没有这一项，误报分析会少一条线索。
        task_goal="non_desktop_task",  # 新增代码+DesktopTaskRouter：使用固定非桌面目标码；如果没有这一项，拒绝结果的目标字段会不稳定。
        requires_gui_actions=False,  # 新增代码+DesktopTaskRouter：拒绝结果不要求 GUI 动作；如果没有这一项，策略层可能误以为需要桌面操作。
        raw_prompt_included=False,  # 新增代码+DesktopTaskRouter：再次明确不保存原始 prompt；如果没有这一项，隐私边界不够显式。
    )  # 新增代码+DesktopTaskRouter：结束非桌面意图对象构造；如果没有这一行，Python 调用语法不完整。


def classify_desktop_task(prompt: str) -> DesktopTaskIntent:  # 修改代码+DesktopTaskRouter：函数段开始，按保守关键词组合把自然语言 prompt 分类为桌面 GUI 任务或普通任务；如果没有这个函数，Task 2 没有实际入口，作者意图是先为 Task 3+ 提供脱敏、可测、误报受控的路由信号，本函数与 DesktopTaskIntent、关键词表和测试文件配合使用，函数段到最后 return 结束为止。
    text = _normalize_prompt(prompt)  # 新增代码+DesktopTaskRouter：规范输入文本用于匹配；如果没有这一行，大小写和空白会让分类结果不稳定。
    if not text:  # 新增代码+DesktopTaskRouter：先处理空 prompt；如果没有这一行，空输入可能继续匹配并产生不可靠结果。
        return _negative_intent("empty_prompt")  # 新增代码+DesktopTaskRouter：空输入返回非桌面任务；如果没有这一行，调用方无法得到稳定拒绝结果。
    target_app_hint = _detect_target_app_hint(text)  # 修改代码+DesktopTaskRouter：提取目标应用提示且英文按词边界；如果没有这一行，painting 会继续误识别成 Paint。
    if _contains_development_keyword(text):  # 修改代码+DesktopTaskRouter：优先应用开发/文档/git/测试误报保护且英文按词边界；如果没有这一行，代码解释和 README/git/test 请求会误入桌面任务。
        return _negative_intent("protected_non_desktop_development_request", target_app_hint)  # 新增代码+DesktopTaskRouter：返回受保护的非桌面结果；如果没有这一行，误报保护命中后仍可能继续被正向规则覆盖。
    has_local_context = _has_local_context(text)  # 修改代码+DesktopTaskRouter：检查是否有本地电脑/桌面上下文且英文按词边界；如果没有这一行，泛化本地应用任务无法安全识别。
    is_paint_gui_task = _has_paint_gui_action(text, target_app_hint, has_local_context)  # 修改代码+DesktopTaskRouter：用明确 Paint 应用名和明确 GUI 操作识别画图桌面任务；如果没有这一行，画图知识问题会继续误路由。
    is_generic_local_gui_task = _has_generic_gui_action(text, has_local_context)  # 修改代码+DesktopTaskRouter：用本地上下文、明确操作和安全应用词识别泛化本地 GUI 任务；如果没有这一行，happy/app 误判无法修复。
    if is_paint_gui_task or is_generic_local_gui_task:  # 新增代码+DesktopTaskRouter：只在正向组合成立时进入桌面任务；如果没有这一行，分类器无法把正负场景分开。
        return DesktopTaskIntent(  # 新增代码+DesktopTaskRouter：返回桌面任务意图对象；如果没有这一行，正向命中无法生成结构化结果。
            is_desktop_task=True,  # 新增代码+DesktopTaskRouter：明确进入桌面任务路线；如果没有这一项，后续不会分流到 Computer Use。
            reason="matched_paint_gui_keywords" if is_paint_gui_task else "matched_local_gui_keywords",  # 新增代码+DesktopTaskRouter：写入脱敏命中原因码；如果没有这一项，后续难以解释分类依据。
            target_app_hint=target_app_hint or "local_app",  # 新增代码+DesktopTaskRouter：写入目标应用提示或泛化本地应用提示；如果没有这一项，后续运行层缺少应用线索。
            task_goal=_task_goal_for(target_app_hint, True),  # 修改代码+DesktopTaskRouter：写入短的类型化任务目标且只在正向命中后传入 True；如果没有这一项，后续可能需要保存原始 prompt 才知道目标。
            requires_gui_actions=True,  # 新增代码+DesktopTaskRouter：明确需要 GUI 动作；如果没有这一项，策略层可能允许脚本绕路。
            raw_prompt_included=False,  # 新增代码+DesktopTaskRouter：明确不包含原始 prompt；如果没有这一项，隐私保护信号不稳定。
        )  # 新增代码+DesktopTaskRouter：结束桌面任务意图对象构造；如果没有这一行，Python 调用语法不完整。
    return _negative_intent("no_local_gui_task_pattern", target_app_hint)  # 新增代码+DesktopTaskRouter：不满足正向组合时保守拒绝；如果没有这一行，普通图片/画图闲聊可能被误判为桌面任务。


__all__ = ("DesktopTaskIntent", "classify_desktop_task")  # 新增代码+DesktopTaskRouter：显式声明本模块公开 API；如果没有这一行，后续导入者不容易知道 Task 2 只暴露意图对象和分类函数。
