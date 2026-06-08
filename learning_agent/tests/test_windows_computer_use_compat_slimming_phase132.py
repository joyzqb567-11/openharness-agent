"""第一批 Computer Use 兼容层瘦身门禁。"""  # 新增代码+CompatSlimming：说明本测试专门防止旧兼容入口继续污染生产链路；如果没有这一行，后续读者不容易知道测试目的。
from __future__ import annotations  # 新增代码+CompatSlimming：启用延迟类型注解；如果没有这一行，跨版本 Python 读取集合类型时更容易出现兼容问题。

import unittest  # 新增代码+CompatSlimming：导入 unittest 测试框架；如果没有这一行，测试类无法被标准测试命令发现和执行。
from pathlib import Path  # 新增代码+CompatSlimming：导入 Path 处理项目路径；如果没有这一行，扫描源码时只能拼接脆弱字符串。

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 新增代码+CompatSlimming：定位 OpenHarness 项目根目录；如果没有这一行，测试在不同工作目录运行会找不到源码。
LEARNING_AGENT_ROOT = PROJECT_ROOT / "learning_agent"  # 新增代码+CompatSlimming：定位 learning_agent 代码根目录；如果没有这一行，扫描范围会不清晰。
LEGACY_MODULE_FILES = {  # 新增代码+CompatSlimming：列出本轮必须迁出的第一批旧兼容文件；如果没有这一段，瘦身验收没有明确边界。
    "learning_agent/computer_use/app_window_control.py",  # 新增代码+CompatSlimming：旧 Phase69 应用窗口控制入口应迁到 resolver/backend/identity；如果没有这一项，旧硬编码计划可能长期留在主链路。
    "learning_agent/computer_use/controlled_app_launch.py",  # 新增代码+CompatSlimming：旧 Phase103 受控启动包装应迁到 generic_launch_backend；如果没有这一项，双启动器会继续制造误接风险。
    "learning_agent/computer_use/generic_app_discovery.py",  # 新增代码+CompatSlimming：旧 Phase108 通用发现包装应迁到 windows_app_inventory/resolver；如果没有这一项，用户指出的旧入口会继续误导判断。
    "learning_agent/computer_use/generic_real_launch_candidate.py",  # 新增代码+CompatSlimming：旧 Phase109 候选包装应迁到 resolver/backend；如果没有这一项，真实启动链路会继续分叉。
    "learning_agent/computer_use/interactive_launch_target.py",  # 新增代码+CompatSlimming：旧 Phase107 交互目标白名单应迁到统一应用清单；如果没有这一项，/computer launch 会继续像白名单功能。
}  # 新增代码+CompatSlimming：结束第一批旧兼容文件清单；如果没有这一行，Python 字面量语法不完整。
LEGACY_IMPORT_TOKENS = tuple(path[:-3].replace("/", ".") for path in sorted(LEGACY_MODULE_FILES))  # 新增代码+CompatSlimming：把旧文件路径转换成包导入名；如果没有这一行，测试无法发现 from/import 形式的旧引用。


def _production_python_files() -> list[Path]:  # 新增代码+CompatSlimming：函数段开始，收集应该被扫描的生产 Python 文件；如果没有这段函数，测试可能误扫学习快照或漏扫生产入口。
    files: list[Path] = []  # 新增代码+CompatSlimming：准备文件列表；如果没有这一行，后续无法累积扫描目标。
    for path in LEARNING_AGENT_ROOT.rglob("*.py"):  # 新增代码+CompatSlimming：递归扫描 learning_agent 下所有 Python 文件；如果没有这一行，测试看不到实际源码引用。
        relative = path.relative_to(PROJECT_ROOT).as_posix()  # 新增代码+CompatSlimming：把绝对路径变成稳定相对路径；如果没有这一行，排除规则会依赖本机盘符。
        if relative.startswith("learning_agent/test/"):  # 新增代码+CompatSlimming：跳过学习快照目录；如果没有这一行，历史归档会让瘦身门禁误报。
            continue  # 新增代码+CompatSlimming：继续扫描下一个文件；如果没有这一行，排除规则不会生效。
        if relative.startswith("learning_agent/tests/"):  # 新增代码+CompatSlimming：跳过测试目录本身；如果没有这一行，测试可包含历史断言会误伤生产判断。
            continue  # 新增代码+CompatSlimming：继续扫描下一个文件；如果没有这一行，测试目录会混入生产引用。
        if relative.startswith("learning_agent/acceptance_controller/runs/"):  # 新增代码+CompatSlimming：跳过验收运行产物；如果没有这一行，旧日志会被误当源码。
            continue  # 新增代码+CompatSlimming：继续扫描下一个文件；如果没有这一行，运行产物排除无效。
        files.append(path)  # 新增代码+CompatSlimming：加入一个生产源码文件；如果没有这一行，测试永远扫描不到文件。
    return files  # 新增代码+CompatSlimming：返回生产源码文件列表；如果没有这一行，调用方拿不到扫描目标。
# 新增代码+CompatSlimming：函数段结束，_production_python_files 到此结束；如果没有这个边界说明，用户不容易看出扫描范围。


def _find_legacy_import_references() -> list[str]:  # 新增代码+CompatSlimming：函数段开始，查找生产源码中的旧兼容导入；如果没有这段函数，测试只能检查文件存在，不能证明主链路是否还引用。
    references: list[str] = []  # 新增代码+CompatSlimming：准备违规引用列表；如果没有这一行，失败信息无法告诉我们迁移范围。
    for path in _production_python_files():  # 新增代码+CompatSlimming：逐个检查生产源码文件；如果没有这一行，测试不会实际读取源码。
        text = path.read_text(encoding="utf-8")  # 新增代码+CompatSlimming：用 UTF-8 读取源码；如果没有这一行，中文注释文件可能因默认编码不同而读取失败。
        relative = path.relative_to(PROJECT_ROOT).as_posix()  # 新增代码+CompatSlimming：生成稳定相对路径；如果没有这一行，失败信息不方便用户定位。
        for token in LEGACY_IMPORT_TOKENS:  # 新增代码+CompatSlimming：逐个旧模块名检查；如果没有这一行，只能检查一个固定旧入口。
            script_token = token.replace("learning_agent.", "")  # 新增代码+CompatSlimming：生成脚本模式导入名；如果没有这一行，start_oauth_agent.bat 的兜底导入可能漏报。
            if token in text or script_token in text:  # 新增代码+CompatSlimming：同时检查包模式和脚本模式导入；如果没有这一行，旧引用会继续藏在 fallback 分支。
                references.append(f"{relative} -> {token}")  # 新增代码+CompatSlimming：记录违规文件和模块；如果没有这一行，失败时不知道该迁移哪里。
    return references  # 新增代码+CompatSlimming：返回全部违规引用；如果没有这一行，断言拿不到事实清单。
# 新增代码+CompatSlimming：函数段结束，_find_legacy_import_references 到此结束；如果没有这个边界说明，用户不容易看出引用扫描范围。


class WindowsComputerUseCompatSlimmingPhase132Test(unittest.TestCase):  # 新增代码+CompatSlimming：测试类段开始，验证第一批兼容层已经从生产链路移除；如果没有这个类，unittest 不会收集本门禁。
    def test_first_batch_legacy_modules_are_not_imported_by_production_code(self) -> None:  # 新增代码+CompatSlimming：测试段开始，检查生产源码不再引用旧兼容模块；如果没有这个测试，旧接口迁移不完整也会被误判完成。
        references = _find_legacy_import_references()  # 新增代码+CompatSlimming：收集旧导入事实；如果没有这一行，断言没有数据来源。
        self.assertEqual([], references)  # 新增代码+CompatSlimming：要求没有任何旧导入；如果没有这一行，旧兼容入口仍可能被误接回主链路。
    # 新增代码+CompatSlimming：测试段结束，test_first_batch_legacy_modules_are_not_imported_by_production_code 到此结束；如果没有这个边界说明，用户不容易看出断言范围。

    def test_first_batch_legacy_module_files_are_removed(self) -> None:  # 新增代码+CompatSlimming：测试段开始，检查第一批旧文件已经删除；如果没有这个测试，旧文件留在源码里会继续误导后续开发。
        existing = [relative for relative in sorted(LEGACY_MODULE_FILES) if (PROJECT_ROOT / relative).exists()]  # 新增代码+CompatSlimming：收集仍存在的旧文件；如果没有这一行，断言无法给出具体删除清单。
        self.assertEqual([], existing)  # 新增代码+CompatSlimming：要求第一批旧文件不存在；如果没有这一行，兼容层瘦身只会停留在“未引用”而不是源码干净。
    # 新增代码+CompatSlimming：测试段结束，test_first_batch_legacy_module_files_are_removed 到此结束；如果没有这个边界说明，用户不容易看出删除门禁范围。
# 新增代码+CompatSlimming：测试类段结束，WindowsComputerUseCompatSlimmingPhase132Test 到此结束；如果没有这个边界说明，用户不容易看出本测试类范围。


if __name__ == "__main__":  # 新增代码+CompatSlimming：文件入口段开始，允许直接运行本测试文件；如果没有这一行，手动排查时只能通过 unittest 模块调用。
    unittest.main()  # 新增代码+CompatSlimming：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+CompatSlimming：文件入口段结束，本测试文件到此结束；如果没有这个边界说明，用户不容易看出脚本入口范围。
