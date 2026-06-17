from __future__ import annotations  # 新增代码+ClipboardRestoreContract：延迟解析类型注解；如果没有这行代码，测试里的现代注解可能在导入时提前求值。

import unittest  # 新增代码+ClipboardRestoreContract：导入 unittest 测试框架；如果没有这行代码，本文件无法声明测试用例。

from learning_agent.computer_use_mcp_v2.windows_runtime.system_clipboard import MemoryClipboardBackend, paste_text_with_restore  # 新增代码+ClipboardRestoreContract：导入内存后端和待测恢复 helper；如果没有这行代码，测试无法验证剪贴板恢复合同。


class ClipboardRestoreContractTests(unittest.TestCase):  # 新增代码+ClipboardRestoreContract：类段开始，集中验证剪贴板临时粘贴恢复合同；如果没有这段类，save/verify/restore 语义缺少自动化保护。
    def test_paste_text_with_restore_restores_original_clipboard(self) -> None:  # 新增代码+ClipboardRestoreContract：函数段开始，验证正常粘贴后恢复原剪贴板；如果没有这段测试，临时写入可能永久覆盖用户剪贴板。
        backend = MemoryClipboardBackend(initial_text="original clipboard")  # 新增代码+ClipboardRestoreContract：准备原始剪贴板文本；如果没有这行代码，测试无法确认恢复回了什么内容。
        pasted: list[str] = []  # 新增代码+ClipboardRestoreContract：记录粘贴回调看到的文本；如果没有这行代码，测试无法证明粘贴发生在临时文本写入之后。

        result = paste_text_with_restore(backend, "typed through clipboard", lambda: pasted.append(backend.text))  # 新增代码+ClipboardRestoreContract：执行临时写入、验证、粘贴和恢复；如果没有这行代码，恢复合同不会被触发。

        self.assertTrue(result["restored"])  # 新增代码+ClipboardRestoreContract：确认最终恢复成功；如果没有这行断言，覆盖用户剪贴板的风险不会暴露。
        self.assertTrue(result["verified_before_paste"])  # 新增代码+ClipboardRestoreContract：确认粘贴前读回验证成功；如果没有这行断言，Ctrl+V 可能粘贴旧内容。
        self.assertTrue(result["pasted"])  # 新增代码+ClipboardRestoreContract：确认粘贴回调已执行；如果没有这行断言，helper 可能只写入不粘贴。
        self.assertEqual(pasted, ["typed through clipboard"])  # 新增代码+ClipboardRestoreContract：确认粘贴时看到临时文本；如果没有这行断言，paste_callback 可能发生在写入前。
        self.assertEqual(backend.text, "original clipboard")  # 新增代码+ClipboardRestoreContract：确认后端内容恢复为原始值；如果没有这行断言，result 标记可能是假恢复。
    # 新增代码+ClipboardRestoreContract：函数段结束，test_paste_text_with_restore_restores_original_clipboard 到此结束；如果没有这个边界说明，用户不容易看出正常恢复测试范围。

    def test_paste_text_with_restore_restores_when_verification_fails(self) -> None:  # 新增代码+ClipboardRestoreContract：函数段开始，验证写入后验证失败也会恢复；如果没有这段测试，失败路径可能留下临时文本。
        class VerificationFailingBackend(MemoryClipboardBackend):  # 新增代码+ClipboardRestoreContract：类段开始，模拟写入后读回不一致的后端；如果没有这段类，验证失败路径难以稳定复现。
            def read_text(self) -> str:  # 新增代码+ClipboardRestoreContract：函数段开始，故意让第二次读取返回错误文本；如果没有这段函数，无法模拟剪贴板被其它进程改写。
                self.read_count += 1  # 新增代码+ClipboardRestoreContract：记录读取次数；如果没有这行代码，后端行为无法按次数变化。
                return "wrong clipboard text" if self.read_count == 2 else self.text  # 新增代码+ClipboardRestoreContract：第二次读取返回错误文本；如果没有这行代码，helper 无法看到验证失败。
            # 新增代码+ClipboardRestoreContract：函数段结束，VerificationFailingBackend.read_text 到此结束；如果没有这个边界说明，用户不容易看出故障模拟范围。
        # 新增代码+ClipboardRestoreContract：类段结束，VerificationFailingBackend 到此结束；如果没有这个边界说明，用户不容易看出测试后端范围。

        backend = VerificationFailingBackend(initial_text="original clipboard")  # 新增代码+ClipboardRestoreContract：准备会验证失败的后端；如果没有这行代码，测试无法触发失败恢复路径。
        pasted: list[str] = []  # 新增代码+ClipboardRestoreContract：记录粘贴回调调用；如果没有这行代码，测试无法证明验证失败时没有粘贴。

        result = paste_text_with_restore(backend, "typed through clipboard", lambda: pasted.append(backend.text))  # 新增代码+ClipboardRestoreContract：执行恢复 helper；如果没有这行代码，失败恢复路径不会被触发。

        self.assertFalse(result["verified_before_paste"])  # 新增代码+ClipboardRestoreContract：确认读回验证失败；如果没有这行断言，测试无法证明进入失败路径。
        self.assertFalse(result["pasted"])  # 新增代码+ClipboardRestoreContract：确认验证失败时没有执行粘贴；如果没有这行断言，错误内容可能被粘贴到真实应用。
        self.assertTrue(result["restored"])  # 新增代码+ClipboardRestoreContract：确认失败路径也恢复原剪贴板；如果没有这行断言，失败会留下临时文本。
        self.assertEqual(pasted, [])  # 新增代码+ClipboardRestoreContract：确认粘贴回调没有运行；如果没有这行断言，验证失败仍可能操作真实窗口。
        self.assertEqual(backend.text, "original clipboard")  # 新增代码+ClipboardRestoreContract：确认后端内容回到原始文本；如果没有这行断言，恢复标记可能是假成功。
    # 新增代码+ClipboardRestoreContract：函数段结束，test_paste_text_with_restore_restores_when_verification_fails 到此结束；如果没有这个边界说明，用户不容易看出失败恢复测试范围。


if __name__ == "__main__":  # 新增代码+ClipboardRestoreContract：允许直接运行本测试文件；如果没有这行代码，手动调试时需要额外 unittest 参数。
    unittest.main()  # 新增代码+ClipboardRestoreContract：启动 unittest 主程序；如果没有这行代码，直接运行文件不会执行测试。
