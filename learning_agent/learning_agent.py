"""learning_agent 的脚本启动入口，不再批量导出核心实现。"""  # 修改代码+LegacyEntryCut: 说明本文件只负责启动 app.cli；若没有这行代码，维护者会继续把这里当成公共 API 聚合层。
from __future__ import annotations  # 修改代码+LegacyEntryCut: 延迟解析类型注解；若没有这行代码，后续入口类型补充更容易受导入顺序影响。

import sys  # 修改代码+LegacyEntryCut: 脚本模式需要调整导入搜索路径；若没有这行代码，双击 bat 启动时可能找不到项目包。
from pathlib import Path  # 修改代码+LegacyEntryCut: 用 Path 计算包目录和项目根目录；若没有这行代码，Windows 路径拼接会更脆弱。

PACKAGE_ROOT = Path(__file__).resolve().parent  # 修改代码+LegacyEntryCut: 定位 learning_agent 包目录；若没有这行代码，脚本模式无法声明子模块搜索范围。
__path__ = [str(PACKAGE_ROOT)]  # 修改代码+LegacyEntryCut: 让同名脚本被误当顶层模块时仍能解析子模块；若没有这行代码，直接运行同目录 MCP server 可能无法导入 learning_agent 子模块。
PROJECT_ROOT = PACKAGE_ROOT.parent  # 修改代码+LegacyEntryCut: 定位 OpenHarness-main 项目根目录；若没有这行代码，直接运行脚本时包路径可能不完整。
PROJECT_ROOT_TEXT = str(PROJECT_ROOT)  # 修改代码+LegacyEntryCut: 把项目根转成 sys.path 需要的字符串；若没有这行代码，路径比较会混用 Path 和 str。
if PROJECT_ROOT_TEXT not in sys.path:  # 修改代码+LegacyEntryCut: 只在缺少项目根时补入搜索路径；若没有这行代码，sys.path 会出现重复项。
    sys.path.insert(0, PROJECT_ROOT_TEXT)  # 修改代码+LegacyEntryCut: 确保 learning_agent 包能被脚本模式导入；若没有这行代码，start_oauth_agent.bat 可能启动失败。

def main() -> None:  # 修改代码+LegacyEntryCut: 延迟导入 app.cli.main 并启动 CLI；若没有这行代码，同名包兜底场景会在顶层导入时形成循环。
    try:  # 修改代码+LegacyEntryCut: 优先按正式包路径导入 app CLI；若没有这行代码，脚本入口无法转交给新 app 层。
        from learning_agent.app.cli import main as app_main  # 修改代码+LegacyEntryCut: 在真正启动时导入 app 主函数；若没有这行代码，python learning_agent\learning_agent.py 无法启动 agent。
    except ModuleNotFoundError as error:  # 修改代码+LegacyEntryCut: 捕获直接脚本模式下包路径暂不可用的情况；若没有这行代码，bat 入口可能在路径边界直接中断。
        if error.name not in {"learning_agent", "learning_agent.app", "learning_agent.app.cli"}:  # 修改代码+LegacyEntryCut: 只允许目标路径缺失时 fallback；若没有这行代码，app 层内部真实 bug 会被误吞。
            raise  # 修改代码+LegacyEntryCut: 非路径问题继续抛出；若没有这行代码，真实导入错误会被伪装成脚本模式问题。
        from app.cli import main as app_main  # 修改代码+LegacyEntryCut: 脚本模式下从同目录 app 包导入 CLI；若没有这行代码，直接运行文件时没有启动入口。
    app_main()  # 修改代码+LegacyEntryCut: 调用 app 层主入口；若没有这行代码，脚本 main 只会导入而不会运行 agent。

__all__ = ["main"]  # 修改代码+LegacyEntryCut: 明确旧脚本文件只公开启动函数；若没有这行代码，外部可能误以为还能从这里拿业务对象。

if __name__ == "__main__":  # 修改代码+LegacyEntryCut: 保留直接运行脚本的行为；若没有这行代码，bat 和命令行启动会打开后立即结束。
    main()  # 修改代码+LegacyEntryCut: 转交给 app.cli.main 处理 CLI、doctor、bridge 和交互模式；若没有这行代码，agent 主程序不会运行。
