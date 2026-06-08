"""支持 python -m learning_agent.harness。"""  # 新增代码+LongTaskHarness: 说明本文件是模块运行入口；若没有这行代码，用户不清楚为什么存在。

from __future__ import annotations  # 新增代码+LongTaskHarness: 延迟解析类型注解；若没有这行代码，入口文件未来扩展更容易受顺序影响。

import sys  # 新增代码+LongTaskHarness: 退出时需要传递 CLI 返回码；若没有这行代码，python -m 无法设置正确退出码。

from learning_agent.harness.cli import main  # 新增代码+LongTaskHarness: 复用 CLI main；若没有这行代码，__main__ 会重复实现命令解析。


if __name__ == "__main__":  # 新增代码+LongTaskHarness: 只在模块直接运行时执行；若没有这行代码，导入包也会触发 CLI。
    raise SystemExit(main(sys.argv[1:]))  # 新增代码+LongTaskHarness: 执行 CLI 并传递退出码；若没有这行代码，python -m 返回码不可靠。
