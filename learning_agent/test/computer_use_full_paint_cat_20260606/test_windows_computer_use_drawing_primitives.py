import math  # 新增代码+DensePikachuPaths：导入 math 计算相邻点距离；如果没有这一行，测试无法判断路径是否足够连续。
import unittest  # 新增代码+DensePikachuPaths：导入 unittest 测试框架；如果没有这一行，标准测试命令无法发现本文件。
from typing import Any  # 新增代码+DensePikachuPaths：导入 Any 标注动态路径字典；如果没有这一行，测试 helper 的输入边界不清楚。

from learning_agent.computer_use.drawing_primitives import build_cat_drag_plan, build_pikachu_drag_plan  # 新增代码+PaintCatSubject：同时导入猫和皮卡丘绘图计划入口；如果没有这一行，测试无法先锁住猫不是皮卡丘/大象的独立 primitive。


def _dense_paths_max_segment(plan: dict[str, Any]) -> float:  # 新增代码+DensePikachuPaths：函数段开始，计算计划里最长相邻点距离；如果没有这个函数，测试只能看事件数量而不能证明线条连续。
    max_distance = 0.0  # 新增代码+DensePikachuPaths：初始化最大距离；如果没有这一行，循环没有可比较基准。
    for path in list(plan.get("drag_paths", []) or []):  # 新增代码+DensePikachuPaths：遍历所有皮卡丘笔画；如果没有这一行，测试不会覆盖每条路径。
        points = list(path.get("points", []) if isinstance(path, dict) else [])  # 新增代码+DensePikachuPaths：读取当前笔画点位；如果没有这一行，后续无法检查相邻点。
        for first, second in zip(points, points[1:]):  # 新增代码+DensePikachuPaths：遍历相邻点对；如果没有这一行，最大距离无法计算。
            dx = int(second.get("x", 0)) - int(first.get("x", 0))  # 新增代码+DensePikachuPaths：计算横向距离；如果没有这一行，距离公式缺少 x 分量。
            dy = int(second.get("y", 0)) - int(first.get("y", 0))  # 新增代码+DensePikachuPaths：计算纵向距离；如果没有这一行，距离公式缺少 y 分量。
            max_distance = max(max_distance, math.hypot(dx, dy))  # 新增代码+DensePikachuPaths：更新最大欧氏距离；如果没有这一行，测试拿不到最长断线长度。
    return max_distance  # 新增代码+DensePikachuPaths：返回最大相邻点距离；如果没有这一行，调用方无法断言连续性。
# 新增代码+DensePikachuPaths：函数段结束，_dense_paths_max_segment 到此结束；如果没有这个边界说明，初学者不容易看出连续性检查范围。


class WindowsComputerUseDrawingPrimitivesTests(unittest.TestCase):  # 新增代码+DensePikachuPaths：类段开始，验证绘图 primitive 的真实鼠标轨迹质量；如果没有这个类，路径质量回归不会被自动发现。
    def test_pikachu_plan_interpolates_dense_continuous_mouse_paths(self) -> None:  # 新增代码+DensePikachuPaths：函数段开始，要求皮卡丘路径足够密，避免真实 Paint 只画几根断线；如果没有这个测试，当前用户问题会复发。
        plan = build_pikachu_drag_plan({"left": 0, "top": 0, "right": 900, "bottom": 700})  # 新增代码+DensePikachuPaths：用真实窗口级画布生成计划；如果没有这一行，测试没有代表性尺寸。
        self.assertGreaterEqual(plan["low_level_event_count"], 320)  # 新增代码+DensePikachuPaths：断言低层事件足够多；如果没有这一行，81 个事件的稀疏计划也会通过。
        self.assertLessEqual(_dense_paths_max_segment(plan), 18.0)  # 新增代码+DensePikachuPaths：断言任意相邻点距离不超过 18 像素；如果没有这一行，长直线会让 Paint 画面缺少可识别轮廓。
        self.assertGreaterEqual(plan["drag_path_count"], 13)  # 新增代码+DensePikachuPaths：断言关键笔画数量仍保留；如果没有这一行，插值时可能丢掉皮卡丘元素。
    # 新增代码+DensePikachuPaths：函数段结束，test_pikachu_plan_interpolates_dense_continuous_mouse_paths 到此结束；如果没有这个边界说明，初学者不容易看出路径密度测试范围。

    def test_cat_plan_has_cat_features_without_pikachu_or_elephant_features(self) -> None:  # 新增代码+PaintCatSubject：函数段开始，验证猫是独立绘图对象而不是皮卡丘/大象替身；如果没有这个测试，用户输入猫时可能继续被旧特例误导。
        plan = build_cat_drag_plan({"left": 0, "top": 0, "right": 900, "bottom": 700})  # 新增代码+PaintCatSubject：用真实窗口级画布生成猫计划；如果没有这一行，测试没有被测计划。
        elements = set(plan["elements"])  # 新增代码+PaintCatSubject：读取猫计划的视觉元素集合；如果没有这一行，断言无法区分猫、皮卡丘和大象。
        self.assertEqual(plan["drawing_subject"], "cat")  # 新增代码+PaintCatSubject：断言报告明确标识猫；如果没有这一行，终端报告可能又写成皮卡丘或大象。
        self.assertIn("cat_ears", elements)  # 新增代码+PaintCatSubject：断言猫耳朵进入计划；如果没有这一行，猫的关键轮廓可能缺失。
        self.assertIn("whiskers", elements)  # 新增代码+PaintCatSubject：断言胡须进入计划；如果没有这一行，猫的识别度会很低。
        self.assertIn("curled_tail", elements)  # 新增代码+PaintCatSubject：断言猫尾巴进入计划；如果没有这一行，动物主体会缺少猫特征。
        self.assertNotIn("lightning_tail", elements)  # 新增代码+PaintCatSubject：断言不能混入皮卡丘闪电尾巴；如果没有这一行，旧皮卡丘特例可能继续伪装成猫。
        self.assertNotIn("trunk", elements)  # 新增代码+PaintCatSubject：断言不能混入大象鼻子；如果没有这一行，旧大象元素可能污染猫计划。
        self.assertGreaterEqual(plan["low_level_event_count"], 260)  # 新增代码+PaintCatSubject：断言猫计划有足够真实鼠标事件；如果没有这一行，几条短线也可能假装完成绘图。
    # 新增代码+PaintCatSubject：函数段结束，test_cat_plan_has_cat_features_without_pikachu_or_elephant_features 到此结束；如果没有这个边界说明，初学者不容易看出猫 primitive 门禁范围。
# 新增代码+DensePikachuPaths：类段结束，WindowsComputerUseDrawingPrimitivesTests 到此结束；如果没有这个边界说明，初学者不容易看出测试集合范围。


if __name__ == "__main__":  # 新增代码+DensePikachuPaths：文件入口段开始，允许直接运行本测试；如果没有这一行，用户必须记住 unittest 模块路径。
    unittest.main()  # 新增代码+DensePikachuPaths：启动 unittest；如果没有这一行，直接运行文件不会执行任何测试。
# 新增代码+DensePikachuPaths：文件入口段结束，直接运行测试到此结束；如果没有这个边界说明，初学者不容易看出脚本入口范围。
