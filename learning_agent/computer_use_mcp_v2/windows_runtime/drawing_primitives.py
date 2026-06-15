"""通用绘图 primitive：把图形计划转换成鼠标拖拽路径。"""  # 新增代码+DrawingPrimitives：说明本模块只生成 GUI 鼠标轨迹计划；如果没有这一行，读者容易误以为这里会直接生成图片文件。
from __future__ import annotations  # 新增代码+DrawingPrimitives：启用延迟类型注解；如果没有这一行，未来返回自身类型或复杂类型时更容易受导入顺序影响。

import math  # 新增代码+DensePikachuPaths：导入 math 用于计算插值步数；如果没有这一行，皮卡丘长线段无法按像素距离补点。
from typing import Any  # 新增代码+DrawingPrimitives：导入 Any 描述来自模型或测试的动态 JSON 值；如果没有这一行，函数签名会缺少清晰边界。


DRAWING_PRIMITIVES_MODEL = "computer_use_drawing_primitives"  # 新增代码+DrawingPrimitives：定义报告模型名；如果没有这一行，成熟矩阵和调试输出难以区分这层证据。
DRAWING_PRIMITIVES_MARKER = "COMPUTER_USE_DRAWING_PRIMITIVES_READY"  # 新增代码+DrawingPrimitives：定义稳定 ready token；如果没有这一行，后续可见终端验收不容易定位绘图 primitive。
DRAWING_PRIMITIVES_OK_TOKEN = "COMPUTER_USE_DRAWING_PRIMITIVES_OK"  # 新增代码+DrawingPrimitives：定义稳定 OK token；如果没有这一行，controller 难以区分普通日志和 primitive 通过。


_PIKACHU_PATH_SPECS: list[dict[str, Any]] = [  # 新增代码+DrawingPrimitives：集中定义皮卡丘相对笔画；如果没有这一组，绘图计划会散落到代表性矩阵里不可复用。
    {"name": "body_outline", "color": "black", "element": "yellow_body", "points": [(0.50, 0.23), (0.43, 0.25), (0.37, 0.34), (0.34, 0.47), (0.36, 0.60), (0.43, 0.70), (0.50, 0.74), (0.57, 0.70), (0.64, 0.60), (0.66, 0.47), (0.63, 0.34), (0.57, 0.25), (0.50, 0.23)]},  # 修改代码+RecognizablePikachuBody：把主体改成更圆的闭合脸身轮廓；如果没有这一笔，真实 Paint 里会只剩耳朵和零散五官。
    {"name": "left_ear", "color": "yellow", "element": "left_ear", "points": [(0.42, 0.28), (0.34, 0.08), (0.39, 0.26)]},  # 新增代码+DrawingPrimitives：定义左耳黄色部分；如果没有这一笔，皮卡丘耳朵不完整。
    {"name": "right_ear", "color": "yellow", "element": "right_ear", "points": [(0.58, 0.28), (0.66, 0.08), (0.61, 0.26)]},  # 新增代码+DrawingPrimitives：定义右耳黄色部分；如果没有这一笔，皮卡丘耳朵不完整。
    {"name": "left_ear_tip", "color": "black", "element": "black_ear_tips", "points": [(0.34, 0.08), (0.37, 0.16), (0.39, 0.10)]},  # 新增代码+DrawingPrimitives：定义左耳黑色耳尖；如果没有这一笔，皮卡丘标志性耳尖会缺失。
    {"name": "right_ear_tip", "color": "black", "element": "black_ear_tips", "points": [(0.66, 0.08), (0.63, 0.16), (0.61, 0.10)]},  # 新增代码+DrawingPrimitives：定义右耳黑色耳尖；如果没有这一笔，皮卡丘标志性耳尖会缺失。
    {"name": "left_eye", "color": "black", "element": "eyes", "points": [(0.45, 0.38), (0.46, 0.40), (0.47, 0.38), (0.46, 0.36), (0.45, 0.38)]},  # 新增代码+DrawingPrimitives：定义左眼小闭合路径；如果没有这一笔，脸部特征会缺少眼睛。
    {"name": "right_eye", "color": "black", "element": "eyes", "points": [(0.55, 0.38), (0.56, 0.40), (0.57, 0.38), (0.56, 0.36), (0.55, 0.38)]},  # 新增代码+DrawingPrimitives：定义右眼小闭合路径；如果没有这一笔，脸部特征会缺少眼睛。
    {"name": "mouth_smile", "color": "black", "element": "mouth", "points": [(0.48, 0.50), (0.50, 0.54), (0.52, 0.50)]},  # 新增代码+DrawingPrimitives：定义微笑嘴巴；如果没有这一笔，皮卡丘表情不完整。
    {"name": "left_cheek", "color": "red", "element": "red_cheeks", "points": [(0.40, 0.50), (0.42, 0.53), (0.44, 0.50), (0.42, 0.47), (0.40, 0.50)]},  # 新增代码+DrawingPrimitives：定义左红脸颊；如果没有这一笔，皮卡丘标志性红脸颊缺失。
    {"name": "right_cheek", "color": "red", "element": "red_cheeks", "points": [(0.60, 0.50), (0.62, 0.53), (0.64, 0.50), (0.62, 0.47), (0.60, 0.50)]},  # 新增代码+DrawingPrimitives：定义右红脸颊；如果没有这一笔，皮卡丘标志性红脸颊缺失。
    {"name": "left_arm", "color": "yellow", "element": "arms", "points": [(0.38, 0.50), (0.30, 0.56), (0.36, 0.58)]},  # 新增代码+DrawingPrimitives：定义左手臂；如果没有这一笔，身体动作感不足。
    {"name": "right_arm", "color": "yellow", "element": "arms", "points": [(0.62, 0.50), (0.70, 0.56), (0.64, 0.58)]},  # 新增代码+DrawingPrimitives：定义右手臂；如果没有这一笔，身体动作感不足。
    {"name": "lightning_tail", "color": "yellow", "element": "lightning_tail", "points": [(0.64, 0.52), (0.78, 0.46), (0.72, 0.58), (0.86, 0.52), (0.76, 0.68)]},  # 新增代码+DrawingPrimitives：定义闪电尾巴；如果没有这一笔，皮卡丘最明显的尾巴特征会缺失。
    {"name": "body_outline_second_pass", "color": "black", "element": "yellow_body", "points": [(0.50, 0.23), (0.43, 0.25), (0.37, 0.34), (0.34, 0.47), (0.36, 0.60), (0.43, 0.70), (0.50, 0.74), (0.57, 0.70), (0.64, 0.60), (0.66, 0.47), (0.63, 0.34), (0.57, 0.25), (0.50, 0.23)]},  # 新增代码+RecognizablePikachuBody：最后再补画一次主体轮廓；如果没有这一笔，Paint 偶发吞掉第一条长拖拽时会再次只留下碎片图形。
]  # 新增代码+DrawingPrimitives：皮卡丘相对笔画定义结束；如果没有这一行，Python 列表语法无法闭合。


_ELEPHANT_PATH_SPECS: list[dict[str, Any]] = [  # 新增代码+GenericPaintSubject：集中定义大象相对笔画；如果没有这一组，大象 prompt 只能继续误用皮卡丘路径。
    {"name": "body_outline", "color": "black", "element": "large_body", "points": [(0.30, 0.45), (0.35, 0.35), (0.48, 0.31), (0.62, 0.36), (0.70, 0.47), (0.68, 0.60), (0.58, 0.68), (0.42, 0.68), (0.31, 0.60), (0.30, 0.45)]},  # 新增代码+GenericPaintSubject：定义大象大身体外轮廓；如果没有这一笔，大象会缺少最主要的体型特征。
    {"name": "head_outline", "color": "black", "element": "head", "points": [(0.60, 0.36), (0.72, 0.34), (0.80, 0.43), (0.77, 0.55), (0.68, 0.58), (0.61, 0.51), (0.60, 0.36)]},  # 新增代码+GenericPaintSubject：定义大象头部轮廓；如果没有这一笔，鼻子和耳朵没有清楚连接点。
    {"name": "left_ear", "color": "black", "element": "large_ears", "points": [(0.61, 0.39), (0.50, 0.30), (0.45, 0.43), (0.52, 0.56), (0.62, 0.50)]},  # 新增代码+GenericPaintSubject：定义左侧大耳朵；如果没有这一笔，大象最醒目的耳朵特征会缺失。
    {"name": "right_ear", "color": "black", "element": "large_ears", "points": [(0.70, 0.39), (0.80, 0.31), (0.86, 0.43), (0.80, 0.55), (0.71, 0.51)]},  # 新增代码+GenericPaintSubject：定义右侧大耳朵；如果没有这一笔，大象头部会不像大象。
    {"name": "trunk", "color": "black", "element": "trunk", "points": [(0.76, 0.52), (0.82, 0.62), (0.80, 0.74), (0.72, 0.78), (0.76, 0.70), (0.75, 0.58)]},  # 新增代码+GenericPaintSubject：定义长鼻子路径；如果没有这一笔，用户要的大象会失去核心识别特征。
    {"name": "tusk_upper", "color": "black", "element": "tusks", "points": [(0.74, 0.56), (0.88, 0.54), (0.76, 0.61)]},  # 新增代码+GenericPaintSubject：定义上方象牙；如果没有这一笔，大象细节会明显不足。
    {"name": "tusk_lower", "color": "black", "element": "tusks", "points": [(0.73, 0.61), (0.86, 0.66), (0.76, 0.66)]},  # 新增代码+GenericPaintSubject：定义下方象牙；如果没有这一笔，象牙结构会太单薄。
    {"name": "front_leg", "color": "black", "element": "legs", "points": [(0.62, 0.63), (0.62, 0.82), (0.68, 0.82), (0.67, 0.64)]},  # 新增代码+GenericPaintSubject：定义前腿；如果没有这一笔，大象身体会像悬空的椭圆。
    {"name": "rear_leg", "color": "black", "element": "legs", "points": [(0.38, 0.63), (0.37, 0.82), (0.43, 0.82), (0.45, 0.65)]},  # 新增代码+GenericPaintSubject：定义后腿；如果没有这一笔，大象站立感不足。
    {"name": "belly_leg_hint", "color": "black", "element": "legs", "points": [(0.48, 0.67), (0.49, 0.80), (0.54, 0.80), (0.55, 0.67)]},  # 新增代码+GenericPaintSubject：定义中部腿部提示线；如果没有这一笔，大象下半身结构会太空。
    {"name": "eye", "color": "black", "element": "eye", "points": [(0.70, 0.43), (0.71, 0.44), (0.72, 0.43), (0.71, 0.42), (0.70, 0.43)]},  # 新增代码+GenericPaintSubject：定义眼睛；如果没有这一笔，大象头部没有表情焦点。
    {"name": "tail", "color": "black", "element": "tail", "points": [(0.31, 0.50), (0.20, 0.44), (0.22, 0.52)]},  # 新增代码+GenericPaintSubject：定义小尾巴；如果没有这一笔，大象身体方向不够清楚。
    {"name": "body_outline_second_pass", "color": "black", "element": "large_body", "points": [(0.30, 0.45), (0.35, 0.35), (0.48, 0.31), (0.62, 0.36), (0.70, 0.47), (0.68, 0.60), (0.58, 0.68), (0.42, 0.68), (0.31, 0.60), (0.30, 0.45)]},  # 新增代码+GenericPaintSubject：再次补画身体轮廓；如果没有这一笔，真实 Paint 偶发吞掉第一条长拖拽时大象主体会残缺。
]  # 新增代码+GenericPaintSubject：大象相对笔画定义结束；如果没有这一行，Python 列表语法无法闭合。


_CAT_PATH_SPECS: list[dict[str, Any]] = [  # 新增代码+PaintCatSubject：集中定义猫的相对笔画；如果没有这一组，猫 prompt 会继续被拒绝或误走旧对象计划。
    {"name": "head_outline", "color": "black", "element": "head", "points": [(0.43, 0.28), (0.36, 0.38), (0.35, 0.52), (0.43, 0.63), (0.55, 0.65), (0.65, 0.57), (0.67, 0.43), (0.61, 0.31), (0.52, 0.25), (0.43, 0.28)]},  # 新增代码+PaintCatSubject：定义猫头圆润外轮廓；如果没有这一笔，猫会缺少主体脸型。
    {"name": "left_cat_ear", "color": "black", "element": "cat_ears", "points": [(0.42, 0.31), (0.36, 0.16), (0.49, 0.27), (0.42, 0.31)]},  # 新增代码+PaintCatSubject：定义左三角猫耳；如果没有这一笔，猫和普通圆脸难以区分。
    {"name": "right_cat_ear", "color": "black", "element": "cat_ears", "points": [(0.56, 0.28), (0.66, 0.15), (0.62, 0.35), (0.56, 0.28)]},  # 新增代码+PaintCatSubject：定义右三角猫耳；如果没有这一笔，猫的头部特征不完整。
    {"name": "left_eye", "color": "black", "element": "eyes", "points": [(0.45, 0.43), (0.46, 0.45), (0.47, 0.43), (0.46, 0.41), (0.45, 0.43)]},  # 新增代码+PaintCatSubject：定义左眼小闭合路径；如果没有这一笔，猫脸没有表情焦点。
    {"name": "right_eye", "color": "black", "element": "eyes", "points": [(0.56, 0.43), (0.57, 0.45), (0.58, 0.43), (0.57, 0.41), (0.56, 0.43)]},  # 新增代码+PaintCatSubject：定义右眼小闭合路径；如果没有这一笔，猫脸会缺少成对眼睛。
    {"name": "nose", "color": "black", "element": "nose", "points": [(0.51, 0.49), (0.49, 0.52), (0.53, 0.52), (0.51, 0.49)]},  # 新增代码+PaintCatSubject：定义小鼻子；如果没有这一笔，胡须和嘴巴没有视觉中心。
    {"name": "mouth", "color": "black", "element": "mouth", "points": [(0.51, 0.52), (0.49, 0.56), (0.47, 0.54), (0.51, 0.52), (0.53, 0.56), (0.56, 0.54)]},  # 新增代码+PaintCatSubject：定义猫嘴曲线；如果没有这一笔，猫脸会显得像无表情圆形。
    {"name": "left_whiskers", "color": "black", "element": "whiskers", "points": [(0.48, 0.51), (0.31, 0.47), (0.48, 0.54), (0.30, 0.55), (0.48, 0.57), (0.32, 0.63)]},  # 新增代码+PaintCatSubject：定义左侧三根胡须；如果没有这一笔，猫最明显的识别特征会缺失。
    {"name": "right_whiskers", "color": "black", "element": "whiskers", "points": [(0.54, 0.51), (0.72, 0.47), (0.54, 0.54), (0.74, 0.55), (0.54, 0.57), (0.72, 0.63)]},  # 新增代码+PaintCatSubject：定义右侧三根胡须；如果没有这一笔，猫脸会左右不完整。
    {"name": "body_outline", "color": "black", "element": "body", "points": [(0.43, 0.63), (0.35, 0.76), (0.44, 0.87), (0.60, 0.86), (0.68, 0.74), (0.61, 0.62)]},  # 新增代码+PaintCatSubject：定义坐姿身体轮廓；如果没有这一笔，猫只剩一个头像无法表达动物主体。
    {"name": "front_paws", "color": "black", "element": "paws", "points": [(0.47, 0.67), (0.47, 0.85), (0.51, 0.78), (0.55, 0.86), (0.55, 0.67)]},  # 新增代码+PaintCatSubject：定义前爪和胸口线；如果没有这一笔，猫身体会缺少站立/坐姿结构。
    {"name": "curled_tail", "color": "black", "element": "curled_tail", "points": [(0.64, 0.72), (0.78, 0.62), (0.82, 0.77), (0.72, 0.87), (0.66, 0.79), (0.74, 0.74)]},  # 新增代码+PaintCatSubject：定义卷尾巴；如果没有这一笔，猫计划缺少区别于大象和皮卡丘的身体特征。
    {"name": "head_outline_second_pass", "color": "black", "element": "head", "points": [(0.43, 0.28), (0.36, 0.38), (0.35, 0.52), (0.43, 0.63), (0.55, 0.65), (0.65, 0.57), (0.67, 0.43), (0.61, 0.31), (0.52, 0.25), (0.43, 0.28)]},  # 新增代码+PaintCatSubject：再次补画猫头轮廓；如果没有这一笔，真实 Paint 偶发吞掉第一条长拖拽时猫脸会残缺。
]  # 新增代码+PaintCatSubject：猫相对笔画定义结束；如果没有这一行，Python 列表语法无法闭合。


def _drawing_safe_int(value: Any, default: int = 0) -> int:  # 新增代码+DrawingPrimitives：函数段开始，把动态坐标安全转成整数；如果没有这段函数，坏坐标可能让绘图计划崩溃。
    try:  # 新增代码+DrawingPrimitives：尝试执行整数转换；如果没有这一行，字符串数字无法兼容。
        return int(value)  # 新增代码+DrawingPrimitives：返回转换后的整数；如果没有这一行，调用方拿不到可用坐标。
    except (TypeError, ValueError):  # 新增代码+DrawingPrimitives：捕获 None、空串或非数字文本；如果没有这一行，模型坏输入会中断任务。
        return int(default)  # 新增代码+DrawingPrimitives：返回默认整数；如果没有这一行，坏坐标没有安全兜底。
# 新增代码+DrawingPrimitives：函数段结束，_drawing_safe_int 到此结束；如果没有这个边界说明，代码小白不容易看出坐标清洗范围。


def _drawing_canvas_rect(canvas_rect: dict[str, Any]) -> dict[str, int]:  # 新增代码+DrawingPrimitives：函数段开始，规范化画布矩形；如果没有这段函数，相对点无法落到受控画布内。
    raw_rect = canvas_rect if isinstance(canvas_rect, dict) else {}  # 新增代码+DrawingPrimitives：只接受字典矩形；如果没有这一行，列表或字符串会导致字段读取异常。
    left = _drawing_safe_int(raw_rect.get("left", 0))  # 新增代码+DrawingPrimitives：读取左边界；如果没有这一行，横向坐标无法计算。
    top = _drawing_safe_int(raw_rect.get("top", 0))  # 新增代码+DrawingPrimitives：读取上边界；如果没有这一行，纵向坐标无法计算。
    right = _drawing_safe_int(raw_rect.get("right", left + 600), left + 600)  # 新增代码+DrawingPrimitives：读取右边界并提供默认宽度；如果没有这一行，缺 right 的画布会退化成零宽。
    bottom = _drawing_safe_int(raw_rect.get("bottom", top + 500), top + 500)  # 新增代码+DrawingPrimitives：读取下边界并提供默认高度；如果没有这一行，缺 bottom 的画布会退化成零高。
    if right <= left:  # 新增代码+DrawingPrimitives：检查横向边界是否有效；如果没有这一行，坏矩形会让所有 x 坐标挤在一起。
        right = left + 600  # 新增代码+DrawingPrimitives：坏宽度时使用保守默认宽度；如果没有这一行，绘图计划不可执行。
    if bottom <= top:  # 新增代码+DrawingPrimitives：检查纵向边界是否有效；如果没有这一行，坏矩形会让所有 y 坐标挤在一起。
        bottom = top + 500  # 新增代码+DrawingPrimitives：坏高度时使用保守默认高度；如果没有这一行，绘图计划不可执行。
    return {"left": left, "top": top, "right": right, "bottom": bottom}  # 新增代码+DrawingPrimitives：返回规范矩形；如果没有这一行，调用方拿不到安全画布。
# 新增代码+DrawingPrimitives：函数段结束，_drawing_canvas_rect 到此结束；如果没有这个边界说明，代码小白不容易看出画布规范化范围。


def _drawing_scale_point(rect: dict[str, int], point: tuple[float, float]) -> dict[str, int]:  # 新增代码+DrawingPrimitives：函数段开始，把相对点缩放成画布绝对坐标；如果没有这段函数，皮卡丘路径不能适配不同窗口大小。
    width = max(1, rect["right"] - rect["left"])  # 新增代码+DrawingPrimitives：计算画布宽度且至少为 1；如果没有这一行，除零或零宽画布会破坏坐标。
    height = max(1, rect["bottom"] - rect["top"])  # 新增代码+DrawingPrimitives：计算画布高度且至少为 1；如果没有这一行，除零或零高画布会破坏坐标。
    x = rect["left"] + round(width * float(point[0]))  # 新增代码+DrawingPrimitives：按相对 x 计算绝对横坐标；如果没有这一行，笔画无法落到画布里。
    y = rect["top"] + round(height * float(point[1]))  # 新增代码+DrawingPrimitives：按相对 y 计算绝对纵坐标；如果没有这一行，笔画无法落到画布里。
    return {"x": int(x), "y": int(y)}  # 新增代码+DrawingPrimitives：返回标准点位字典；如果没有这一行，通用输入层无法直接消费。
# 新增代码+DrawingPrimitives：函数段结束，_drawing_scale_point 到此结束；如果没有这个边界说明，代码小白不容易看出缩放范围。


def _drawing_point(value: Any) -> dict[str, int]:  # 新增代码+DrawingPrimitives：函数段开始，兼容 tuple/list/dict 三种点位输入；如果没有这段函数，测试和动作层必须使用同一种脆弱格式。
    if isinstance(value, dict):  # 新增代码+DrawingPrimitives：处理字典点位；如果没有这一行，计划中的 {"x": 1, "y": 2} 无法展开。
        return {"x": _drawing_safe_int(value.get("x", 0)), "y": _drawing_safe_int(value.get("y", 0))}  # 新增代码+DrawingPrimitives：返回清洗后的字典点位；如果没有这一行，坐标可能保持坏类型。
    if isinstance(value, (list, tuple)) and len(value) >= 2:  # 新增代码+DrawingPrimitives：处理 tuple/list 点位；如果没有这一行，[(10, 10)] 这种自然输入无法展开。
        return {"x": _drawing_safe_int(value[0]), "y": _drawing_safe_int(value[1])}  # 新增代码+DrawingPrimitives：返回 tuple/list 的前两个坐标；如果没有这一行，测试样本无法通过。
    return {"x": 0, "y": 0}  # 新增代码+DrawingPrimitives：坏点位兜底到原点；如果没有这一行，单个坏点可能中断整条路径。
# 新增代码+DrawingPrimitives：函数段结束，_drawing_point 到此结束；如果没有这个边界说明，代码小白不容易看出点位兼容范围。


def _drawing_interpolate_points(points: list[dict[str, int]], max_step_pixels: int = 14) -> list[dict[str, int]]:  # 新增代码+DensePikachuPaths：函数段开始，把少量端点补成连续鼠标轨迹；如果没有这个函数，真实 Paint 只会留下几根稀疏长线。
    safe_points = [_drawing_point(point) for point in list(points or [])]  # 新增代码+DensePikachuPaths：清洗输入点；如果没有这一行，坏点位会直接破坏插值计算。
    if len(safe_points) < 2:  # 新增代码+DensePikachuPaths：少于两个点没有线段可补；如果没有这一行，空路径会进入后续循环。
        return safe_points  # 新增代码+DensePikachuPaths：返回原始安全点；如果没有这一行，单点路径会被错误清空。
    dense_points: list[dict[str, int]] = [dict(safe_points[0])]  # 新增代码+DensePikachuPaths：保留第一点作为拖拽起点；如果没有这一行，鼠标按下起点会丢失。
    step_limit = max(1, int(max_step_pixels))  # 新增代码+DensePikachuPaths：规范化最大步长且至少为 1；如果没有这一行，0 或负数会导致除零。
    for start, end in zip(safe_points, safe_points[1:]):  # 新增代码+DensePikachuPaths：遍历每一段原始线段；如果没有这一行，无法给长线补点。
        dx = int(end["x"]) - int(start["x"])  # 新增代码+DensePikachuPaths：计算横向跨度；如果没有这一行，插值不知道 x 方向要走多远。
        dy = int(end["y"]) - int(start["y"])  # 新增代码+DensePikachuPaths：计算纵向跨度；如果没有这一行，插值不知道 y 方向要走多远。
        distance = math.hypot(dx, dy)  # 新增代码+DensePikachuPaths：计算线段长度；如果没有这一行，无法按像素距离决定补点数量。
        steps = max(1, int(math.ceil(distance / step_limit)))  # 新增代码+DensePikachuPaths：计算需要拆成多少小步；如果没有这一行，长线仍然只有一个跳跃点。
        for index in range(1, steps + 1):  # 新增代码+DensePikachuPaths：逐步生成插值点；如果没有这一行，dense_points 不会增加。
            ratio = index / steps  # 新增代码+DensePikachuPaths：计算当前位置在线段中的比例；如果没有这一行，无法从起点走到终点。
            dense_points.append({"x": int(round(start["x"] + dx * ratio)), "y": int(round(start["y"] + dy * ratio))})  # 新增代码+DensePikachuPaths：追加当前插值点；如果没有这一行，真实鼠标路径仍不连续。
    return dense_points  # 新增代码+DensePikachuPaths：返回补点后的连续路径；如果没有这一行，调用方拿不到成熟轨迹。
# 新增代码+DensePikachuPaths：函数段结束，_drawing_interpolate_points 到此结束；如果没有这个边界说明，代码小白不容易看出路径加密范围。


def expand_drag_path_to_low_level_events(points: list[Any]) -> list[dict[str, Any]]:  # 新增代码+DrawingPrimitives：函数段开始，把拖拽路径展开为底层鼠标事件；如果没有这段函数，drag_path 只是描述不能执行。
    safe_points = [_drawing_point(point) for point in list(points or [])]  # 新增代码+DrawingPrimitives：清洗所有点位；如果没有这一行，坏点位会直接污染事件。
    if len(safe_points) < 2:  # 新增代码+DrawingPrimitives：至少需要起点和终点；如果没有这一行，单点路径会生成半个拖拽。
        return []  # 新增代码+DrawingPrimitives：点数不足时返回零事件；如果没有这一行，调用方无法做零事件拒绝。
    events: list[dict[str, Any]] = [{"type": "mouse_move", "x": safe_points[0]["x"], "y": safe_points[0]["y"], "path_index": 0, "real_dispatch_allowed": False}, {"type": "mouse_down", "button": "left", "x": safe_points[0]["x"], "y": safe_points[0]["y"], "real_dispatch_allowed": False}]  # 新增代码+DrawingPrimitives：先移动到起点并按下鼠标；如果没有这一行，绘制会从未知位置开始。
    for index, point in enumerate(safe_points[1:], start=1):  # 新增代码+DrawingPrimitives：遍历后续路径点；如果没有这一行，拖拽不会形成连续轨迹。
        events.append({"type": "mouse_move", "x": point["x"], "y": point["y"], "path_index": index, "real_dispatch_allowed": False})  # 新增代码+DrawingPrimitives：追加每个路径点的移动事件；如果没有这一行，线条会丢点。
    events.append({"type": "mouse_up", "button": "left", "x": safe_points[-1]["x"], "y": safe_points[-1]["y"], "real_dispatch_allowed": False})  # 新增代码+DrawingPrimitives：在终点抬起鼠标；如果没有这一行，拖拽不会闭合。
    return events  # 新增代码+DrawingPrimitives：返回完整低层事件序列；如果没有这一行，dispatcher 拿不到可发送动作。
# 新增代码+DrawingPrimitives：函数段结束，expand_drag_path_to_low_level_events 到此结束；如果没有这个边界说明，代码小白不容易看出拖拽展开范围。


def build_pikachu_drag_plan(canvas_rect: dict[str, Any]) -> dict[str, Any]:  # 新增代码+DrawingPrimitives：函数段开始，构建不写图片文件的皮卡丘拖拽计划；如果没有这段函数，画图任务只能依赖固定矩阵或脚本绕路。
    rect = _drawing_canvas_rect(canvas_rect)  # 新增代码+DrawingPrimitives：规范化画布区域；如果没有这一行，相对笔画无法变成窗口内坐标。
    drag_paths: list[dict[str, Any]] = []  # 新增代码+DrawingPrimitives：准备笔画列表；如果没有这一行，后续无法累积路径。
    for spec in _PIKACHU_PATH_SPECS:  # 新增代码+DrawingPrimitives：遍历每条皮卡丘相对笔画；如果没有这一行，计划不会包含任何视觉元素。
        raw_points = [_drawing_scale_point(rect, point) for point in spec["points"]]  # 修改代码+DensePikachuPaths：先把相对端点缩放到当前画布；如果没有这一行，插值没有绝对坐标输入。
        points = _drawing_interpolate_points(raw_points, max_step_pixels=10)  # 修改代码+DensePikachuPaths：用更短步长补成密集鼠标轨迹；如果没有这一行，真实 Paint 仍可能只留下稀疏线段。
        events = expand_drag_path_to_low_level_events(points)  # 新增代码+DrawingPrimitives：预先生成事件摘要；如果没有这一行，计划无法量化低层事件数。
        drag_paths.append({"action": "drag_path", "name": spec["name"], "color": spec["color"], "element": spec["element"], "points": points, "event_count": len(events), "continuous_mouse_path": bool(events and events[0].get("type") == "mouse_move" and any(event.get("type") == "mouse_down" for event in events) and any(event.get("type") == "mouse_up" for event in events)), "real_dispatch_allowed": False})  # 新增代码+DrawingPrimitives：保存单条通用拖拽动作；如果没有这一行，调用方拿不到可执行笔画。
    colors = sorted({str(path["color"]) for path in drag_paths})  # 新增代码+DrawingPrimitives：汇总颜色集合；如果没有这一行，计划无法证明黄色/黑色/红色齐全。
    elements = sorted({str(path["element"]) for path in drag_paths})  # 新增代码+DrawingPrimitives：汇总视觉元素集合；如果没有这一行，计划无法证明关键皮卡丘元素齐全。
    low_level_event_count = sum(_drawing_safe_int(path.get("event_count", 0)) for path in drag_paths)  # 新增代码+DrawingPrimitives：累计底层事件数量；如果没有这一行，成熟验收无法判断动作密度。
    return {"marker": DRAWING_PRIMITIVES_MARKER, "ok_token": DRAWING_PRIMITIVES_OK_TOKEN, "model": DRAWING_PRIMITIVES_MODEL, "passed": True, "canvas_rect": rect, "drag_paths": drag_paths, "drag_path_count": len(drag_paths), "gui_action_count": len(drag_paths), "low_level_event_count": low_level_event_count, "colors": colors, "elements": elements, "drawing_primitive_used": True, "direct_image_file_cheat": False, "image_file_written": False, "real_desktop_touched": False}  # 新增代码+DrawingPrimitives：返回完整计划报告；如果没有这一行，测试、runtime 和矩阵无法共享绘图 primitive 事实。
# 新增代码+DrawingPrimitives：函数段结束，build_pikachu_drag_plan 到此结束；如果没有这个边界说明，代码小白不容易看出皮卡丘计划构造范围。


def build_elephant_drag_plan(canvas_rect: dict[str, Any]) -> dict[str, Any]:  # 新增代码+GenericPaintSubject：函数段开始，构建不写图片文件的大象拖拽计划；如果没有这段函数，大象 prompt 仍会被迫走皮卡丘硬编码。
    rect = _drawing_canvas_rect(canvas_rect)  # 新增代码+GenericPaintSubject：规范化画布区域；如果没有这一行，大象相对笔画无法变成窗口内坐标。
    drag_paths: list[dict[str, Any]] = []  # 新增代码+GenericPaintSubject：准备大象笔画列表；如果没有这一行，后续无法累积路径。
    for spec in _ELEPHANT_PATH_SPECS:  # 新增代码+GenericPaintSubject：遍历每条大象相对笔画；如果没有这一行，计划不会包含鼻子、耳朵和腿。
        raw_points = [_drawing_scale_point(rect, point) for point in spec["points"]]  # 新增代码+GenericPaintSubject：先把相对端点缩放到当前画布；如果没有这一行，插值没有绝对坐标输入。
        points = _drawing_interpolate_points(raw_points, max_step_pixels=10)  # 新增代码+GenericPaintSubject：把大象路径补成密集鼠标轨迹；如果没有这一行，真实 Paint 可能只留下几条断线。
        events = expand_drag_path_to_low_level_events(points)  # 新增代码+GenericPaintSubject：预先生成事件摘要；如果没有这一行，计划无法量化低层事件数。
        drag_paths.append({"action": "drag_path", "name": spec["name"], "color": spec["color"], "element": spec["element"], "points": points, "event_count": len(events), "continuous_mouse_path": bool(events and events[0].get("type") == "mouse_move" and any(event.get("type") == "mouse_down" for event in events) and any(event.get("type") == "mouse_up" for event in events)), "real_dispatch_allowed": False})  # 新增代码+GenericPaintSubject：保存单条大象拖拽动作；如果没有这一行，调用方拿不到可执行笔画。
    colors = sorted({str(path["color"]) for path in drag_paths})  # 新增代码+GenericPaintSubject：汇总颜色集合；如果没有这一行，报告无法证明大象计划颜色来源。
    elements = sorted({str(path["element"]) for path in drag_paths})  # 新增代码+GenericPaintSubject：汇总大象视觉元素集合；如果没有这一行，测试无法确认鼻子和大耳朵存在。
    low_level_event_count = sum(_drawing_safe_int(path.get("event_count", 0)) for path in drag_paths)  # 新增代码+GenericPaintSubject：累计底层事件数量；如果没有这一行，成熟验收无法判断动作密度。
    return {"marker": DRAWING_PRIMITIVES_MARKER, "ok_token": DRAWING_PRIMITIVES_OK_TOKEN, "model": DRAWING_PRIMITIVES_MODEL, "passed": True, "drawing_subject": "elephant", "canvas_rect": rect, "drag_paths": drag_paths, "drag_path_count": len(drag_paths), "gui_action_count": len(drag_paths), "low_level_event_count": low_level_event_count, "colors": colors, "elements": elements, "drawing_primitive_used": True, "direct_image_file_cheat": False, "image_file_written": False, "real_desktop_touched": False}  # 新增代码+GenericPaintSubject：返回完整大象计划报告；如果没有这一行，runtime 无法证明大象不是皮卡丘替身。
# 新增代码+GenericPaintSubject：函数段结束，build_elephant_drag_plan 到此结束；如果没有这个边界说明，代码小白不容易看出大象计划构造范围。


def build_cat_drag_plan(canvas_rect: dict[str, Any]) -> dict[str, Any]:  # 新增代码+PaintCatSubject：函数段开始，构建不写图片文件的猫拖拽计划；如果没有这段函数，猫 prompt 无法进入真实 Paint 绘图闭环。
    rect = _drawing_canvas_rect(canvas_rect)  # 新增代码+PaintCatSubject：规范化画布区域；如果没有这一行，猫相对笔画无法变成窗口内坐标。
    drag_paths: list[dict[str, Any]] = []  # 新增代码+PaintCatSubject：准备猫笔画列表；如果没有这一行，后续无法累积路径。
    for spec in _CAT_PATH_SPECS:  # 新增代码+PaintCatSubject：遍历每条猫相对笔画；如果没有这一行，计划不会包含耳朵、胡须和尾巴。
        raw_points = [_drawing_scale_point(rect, point) for point in spec["points"]]  # 新增代码+PaintCatSubject：先把相对端点缩放到当前画布；如果没有这一行，插值没有绝对坐标输入。
        points = _drawing_interpolate_points(raw_points, max_step_pixels=10)  # 新增代码+PaintCatSubject：把猫路径补成密集鼠标轨迹；如果没有这一行，真实 Paint 可能只留下几条断线。
        events = expand_drag_path_to_low_level_events(points)  # 新增代码+PaintCatSubject：预先生成事件摘要；如果没有这一行，计划无法量化低层事件数。
        drag_paths.append({"action": "drag_path", "name": spec["name"], "color": spec["color"], "element": spec["element"], "points": points, "event_count": len(events), "continuous_mouse_path": bool(events and events[0].get("type") == "mouse_move" and any(event.get("type") == "mouse_down" for event in events) and any(event.get("type") == "mouse_up" for event in events)), "real_dispatch_allowed": False})  # 新增代码+PaintCatSubject：保存单条猫拖拽动作；如果没有这一行，调用方拿不到可执行笔画。
    colors = sorted({str(path["color"]) for path in drag_paths})  # 新增代码+PaintCatSubject：汇总颜色集合；如果没有这一行，报告无法证明猫计划颜色来源。
    elements = sorted({str(path["element"]) for path in drag_paths})  # 新增代码+PaintCatSubject：汇总猫视觉元素集合；如果没有这一行，测试无法确认耳朵、胡须和尾巴存在。
    low_level_event_count = sum(_drawing_safe_int(path.get("event_count", 0)) for path in drag_paths)  # 新增代码+PaintCatSubject：累计底层事件数量；如果没有这一行，成熟验收无法判断动作密度。
    return {"marker": DRAWING_PRIMITIVES_MARKER, "ok_token": DRAWING_PRIMITIVES_OK_TOKEN, "model": DRAWING_PRIMITIVES_MODEL, "passed": True, "drawing_subject": "cat", "canvas_rect": rect, "drag_paths": drag_paths, "drag_path_count": len(drag_paths), "gui_action_count": len(drag_paths), "low_level_event_count": low_level_event_count, "colors": colors, "elements": elements, "drawing_primitive_used": True, "direct_image_file_cheat": False, "image_file_written": False, "real_desktop_touched": False}  # 新增代码+PaintCatSubject：返回完整猫计划报告；如果没有这一行，runtime 无法证明猫不是皮卡丘或大象替身。
# 新增代码+PaintCatSubject：函数段结束，build_cat_drag_plan 到此结束；如果没有这个边界说明，代码小白不容易看出猫计划构造范围。


__all__ = ["DRAWING_PRIMITIVES_MARKER", "DRAWING_PRIMITIVES_MODEL", "DRAWING_PRIMITIVES_OK_TOKEN", "build_cat_drag_plan", "build_elephant_drag_plan", "build_pikachu_drag_plan", "expand_drag_path_to_low_level_events"]  # 修改代码+PaintCatSubject：把猫计划加入公开 API；如果没有这一行，Paint 真实闭环无法按用户 prompt 调用猫计划。
