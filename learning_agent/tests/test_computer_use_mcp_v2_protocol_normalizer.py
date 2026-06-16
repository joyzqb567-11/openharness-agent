from __future__ import annotations  # 新增代码+ClaudeCodeProtocolParityTests：延迟类型注解解析；如果没有这行代码，测试导入时类型求值更容易出错。

import unittest  # 新增代码+ClaudeCodeProtocolParityTests：导入 unittest 框架；如果没有这行代码，测试类不会执行。

from learning_agent.computer_use_mcp_v2.inferred_ant_mcp.protocol_normalizer import normalize_computer_use_arguments  # 新增代码+ClaudeCodeProtocolParityTests：导入协议参数归一化入口；如果没有这行代码，测试无法验证 ClaudeCode 字段转换。


class ComputerUseMcpV2ProtocolNormalizerTests(unittest.TestCase):  # 新增代码+ClaudeCodeProtocolParityTests：类段开始，验证 ClaudeCode 字段到 Windows runtime 字段的转换；如果没有这段类，normalizer 没有自动化保护。
    def test_coordinate_array_becomes_xy_for_windows_runtime(self) -> None:  # 新增代码+ClaudeCodeProtocolParityTests：函数段开始，验证 coordinate 转 x/y；如果没有这段测试，点击工具可能收不到 Windows 坐标。
        normalized = normalize_computer_use_arguments("left_click", {"coordinate": [12, 34]})  # 新增代码+ClaudeCodeProtocolParityTests：用 ClaudeCode 坐标调用 normalizer；如果没有这行代码，测试没有输入。
        self.assertEqual(normalized["x"], 12)  # 新增代码+ClaudeCodeProtocolParityTests：断言 x 被补齐；如果没有这行代码，横坐标转换错误不会失败。
        self.assertEqual(normalized["y"], 34)  # 新增代码+ClaudeCodeProtocolParityTests：断言 y 被补齐；如果没有这行代码，纵坐标转换错误不会失败。
        self.assertEqual(normalized["coordinate"], [12, 34])  # 新增代码+ClaudeCodeProtocolParityTests：断言原 coordinate 保留；如果没有这行代码，审计和 ClaudeCode-facing 结果会丢字段。
    # 新增代码+ClaudeCodeProtocolParityTests：函数段结束，test_coordinate_array_becomes_xy_for_windows_runtime 到此结束；如果没有这个边界说明，用户不容易看出坐标转换测试范围。

    def test_drag_start_coordinate_and_coordinate_become_start_end_xy(self) -> None:  # 新增代码+ClaudeCodeProtocolParityTests：函数段开始，验证拖拽起点终点转换；如果没有这段测试，drag_path 会缺坐标。
        normalized = normalize_computer_use_arguments("left_click_drag", {"start_coordinate": [1, 2], "coordinate": [30, 40]})  # 新增代码+ClaudeCodeProtocolParityTests：用 ClaudeCode 拖拽字段调用 normalizer；如果没有这行代码，测试无法覆盖起点终点。
        self.assertEqual(normalized["start_x"], 1)  # 新增代码+ClaudeCodeProtocolParityTests：断言起点 x 被补齐；如果没有这行代码，拖拽起点横坐标可能丢失。
        self.assertEqual(normalized["start_y"], 2)  # 新增代码+ClaudeCodeProtocolParityTests：断言起点 y 被补齐；如果没有这行代码，拖拽起点纵坐标可能丢失。
        self.assertEqual(normalized["end_x"], 30)  # 新增代码+ClaudeCodeProtocolParityTests：断言终点 x 被补齐；如果没有这行代码，拖拽终点横坐标可能丢失。
        self.assertEqual(normalized["end_y"], 40)  # 新增代码+ClaudeCodeProtocolParityTests：断言终点 y 被补齐；如果没有这行代码，拖拽终点纵坐标可能丢失。
    # 新增代码+ClaudeCodeProtocolParityTests：函数段结束，test_drag_start_coordinate_and_coordinate_become_start_end_xy 到此结束；如果没有这个边界说明，用户不容易看出拖拽转换测试范围。

    def test_region_array_becomes_xy_width_height(self) -> None:  # 新增代码+ClaudeCodeProtocolParityTests：函数段开始，验证 region 转 x/y/width/height；如果没有这段测试，zoom 无法复用 Windows 裁剪链。
        normalized = normalize_computer_use_arguments("zoom", {"region": [10, 20, 300, 200]})  # 新增代码+ClaudeCodeProtocolParityTests：用 ClaudeCode region 调用 normalizer；如果没有这行代码，测试没有区域输入。
        self.assertEqual(normalized["x"], 10)  # 新增代码+ClaudeCodeProtocolParityTests：断言区域 x 被补齐；如果没有这行代码，zoom 左上角横坐标会错。
        self.assertEqual(normalized["y"], 20)  # 新增代码+ClaudeCodeProtocolParityTests：断言区域 y 被补齐；如果没有这行代码，zoom 左上角纵坐标会错。
        self.assertEqual(normalized["width"], 300)  # 新增代码+ClaudeCodeProtocolParityTests：断言区域宽度被补齐；如果没有这行代码，zoom 裁剪宽度会缺失。
        self.assertEqual(normalized["height"], 200)  # 新增代码+ClaudeCodeProtocolParityTests：断言区域高度被补齐；如果没有这行代码，zoom 裁剪高度会缺失。
    # 新增代码+ClaudeCodeProtocolParityTests：函数段结束，test_region_array_becomes_xy_width_height 到此结束；如果没有这个边界说明，用户不容易看出区域转换测试范围。

    def test_bundle_id_is_preserved_and_mirrored_to_app_name_for_legacy_runtime(self) -> None:  # 新增代码+ClaudeCodeProtocolParityTests：函数段开始，验证 bundle_id 兼容 app_name；如果没有这段测试，open_application 会断 Windows 旧执行层。
        normalized = normalize_computer_use_arguments("open_application", {"bundle_id": "notepad.exe"})  # 新增代码+ClaudeCodeProtocolParityTests：用 ClaudeCode 应用字段调用 normalizer；如果没有这行代码，测试没有应用输入。
        self.assertEqual(normalized["bundle_id"], "notepad.exe")  # 新增代码+ClaudeCodeProtocolParityTests：断言原 bundle_id 保留；如果没有这行代码，ClaudeCode-facing 审计会丢应用身份。
        self.assertEqual(normalized["app_name"], "notepad.exe")  # 新增代码+ClaudeCodeProtocolParityTests：断言旧 app_name 被补齐；如果没有这行代码，Windows runtime 找不到目标应用。
    # 新增代码+ClaudeCodeProtocolParityTests：函数段结束，test_bundle_id_is_preserved_and_mirrored_to_app_name_for_legacy_runtime 到此结束；如果没有这个边界说明，用户不容易看出应用字段转换范围。

    def test_apps_are_normalized_and_mirrored_to_applications(self) -> None:  # 新增代码+ClaudeCodeProtocolParityTests：函数段开始，验证 request_access apps 转 applications；如果没有这段测试，权限层会收到混合字段。
        normalized = normalize_computer_use_arguments("request_access", {"apps": [{"displayName": "Notepad", "bundleId": "notepad.exe"}]})  # 新增代码+ClaudeCodeProtocolParityTests：用 ClaudeCode app 对象调用 normalizer；如果没有这行代码，测试无法覆盖 app allowlist。
        self.assertEqual(normalized["apps"][0]["displayName"], "Notepad")  # 新增代码+ClaudeCodeProtocolParityTests：断言 app 展示名保留；如果没有这行代码，权限提示可能没有人类可读名称。
        self.assertEqual(normalized["apps"][0]["bundleId"], "notepad.exe")  # 新增代码+ClaudeCodeProtocolParityTests：断言 bundleId 保留；如果没有这行代码，权限状态无法稳定匹配应用。
        self.assertEqual(normalized["applications"], ["Notepad"])  # 新增代码+ClaudeCodeProtocolParityTests：断言旧 applications 兼容字段被补齐；如果没有这行代码，旧权限回调会丢目标应用。
    # 新增代码+ClaudeCodeProtocolParityTests：函数段结束，test_apps_are_normalized_and_mirrored_to_applications 到此结束；如果没有这个边界说明，用户不容易看出授权字段转换范围。

    def test_actions_are_mirrored_to_steps_for_legacy_batch_runtime(self) -> None:  # 新增代码+ClaudeCodeProtocolParityTests：函数段开始，验证 batch actions 转 steps；如果没有这段测试，旧 batch adapter 可能读不到步骤。
        normalized = normalize_computer_use_arguments("computer_batch", {"actions": [{"tool": "wait", "arguments": {"seconds": 1}}]})  # 新增代码+ClaudeCodeProtocolParityTests：用 ClaudeCode actions 调用 normalizer；如果没有这行代码，测试没有 batch 输入。
        self.assertEqual(normalized["steps"], normalized["actions"])  # 新增代码+ClaudeCodeProtocolParityTests：断言 steps 兼容字段被补齐；如果没有这行代码，旧 batch 路径可能空执行。
    # 新增代码+ClaudeCodeProtocolParityTests：函数段结束，test_actions_are_mirrored_to_steps_for_legacy_batch_runtime 到此结束；如果没有这个边界说明，用户不容易看出 batch 字段转换范围。


if __name__ == "__main__":  # 新增代码+ClaudeCodeProtocolParityTests：允许直接运行本测试文件；如果没有这行代码，手动调试不方便。
    unittest.main()  # 新增代码+ClaudeCodeProtocolParityTests：启动 unittest；如果没有这行代码，直接运行文件不会执行测试。
