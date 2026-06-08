"""浏览器视觉证据录制：保存帧序列、manifest，并导出 GIF。"""  # 新增代码+BrowserRecordingStage9: 说明本模块负责可审计视觉证据；若没有这行代码，录制职责会散落在 MCP server 里。

from __future__ import annotations  # 新增代码+BrowserRecordingStage9: 延迟解析类型注解；若没有这行代码，返回类型在旧解释顺序下更脆弱。

import argparse  # 新增代码+BrowserRecordingStage9: 提供 `python -m learning_agent.browser.recording --selftest` 入口；若没有这行代码，真实验收无法独立生成录制产物。
import re  # 新增代码+BrowserRecordingStage9: 清洗 recording_id 和输出文件名；若没有这行代码，用户输入可能生成危险路径。
import secrets  # 新增代码+BrowserRecordingStage9: 没有传 recording_id 时生成唯一 id；若没有这行代码，多次录制容易撞名。
from pathlib import Path  # 新增代码+BrowserRecordingStage9: 管理 Windows 路径和 artifact 目录；若没有这行代码，帧和 GIF 路径拼接会脆弱。
from typing import Any  # 新增代码+BrowserRecordingStage9: manifest 是通用 JSON 字典；若没有这行代码，类型边界不清楚。

from PIL import Image  # 新增代码+BrowserRecordingStage9: 使用 Pillow 把 PNG 帧导出为 GIF；若没有这行代码，Stage 9 只能保存静态帧。

try:  # 新增代码+BrowserRecordingStage9: 优先按包路径导入项目 helper；若没有这行代码，标准包运行和测试无法共享实现。
    from learning_agent.browser.runtime_models import now_ms  # 新增代码+BrowserRecordingStage9: 复用统一毫秒时间戳；若没有这行代码，录制时间线会和 browser runtime 分裂。
    from learning_agent.runtime.files import atomic_write_json, read_json_or_default  # 新增代码+BrowserRecordingStage9: 复用原子写和容错读；若没有这行代码，manifest 半写会破坏恢复。
except ModuleNotFoundError as import_error:  # 新增代码+BrowserRecordingStage9: 兼容本模块被直接脚本路径导入；若没有这行代码，stdio MCP server 脚本模式可能找不到 learning_agent 包。
    if import_error.name not in {"learning_agent", "learning_agent.browser", "learning_agent.browser.runtime_models", "learning_agent.runtime", "learning_agent.runtime.files"}:  # 新增代码+BrowserRecordingStage9: 只对目标路径缺失做 fallback；若没有这行代码，内部真实错误会被误吞。
        raise  # 新增代码+BrowserRecordingStage9: 重新抛出真实导入错误；若没有这行代码，排查会被错误 fallback 误导。
    from runtime.files import atomic_write_json, read_json_or_default  # 新增代码+BrowserRecordingStage9: 脚本模式导入 runtime 文件 helper；若没有这行代码，直接运行时 manifest 不能原子写。
    from browser.runtime_models import now_ms  # 新增代码+BrowserRecordingStage9: 脚本模式导入时间 helper；若没有这行代码，直接运行时录制时间线不稳定。


def _safe_name(value: str, default: str) -> str:  # 新增代码+BrowserRecordingStage9: 把用户传入名字清洗成安全文件名；若没有这行代码，`../` 可能逃出录制目录。
    raw = str(value or "").strip()  # 新增代码+BrowserRecordingStage9: 先把输入转成去空白字符串；若没有这行代码，None 或空格会进入文件名。
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)[:120].strip("._-")  # 新增代码+BrowserRecordingStage9: 只保留安全字符并限制长度；若没有这行代码，路径可能不可移植或过长。
    return cleaned or default  # 新增代码+BrowserRecordingStage9: 空名字使用默认值；若没有这行代码，可能生成空目录名。


class BrowserRecordingStore:  # 新增代码+BrowserRecordingStage9: 管理浏览器录制 manifest、帧和 GIF；若没有这个类，工具层会直接操作散落文件。
    def __init__(self, base_dir: str | Path) -> None:  # 新增代码+BrowserRecordingStage9: 初始化录制根目录；若没有这行代码，测试和生产无法指定不同 artifact 根。
        self.base_dir = Path(base_dir)  # 新增代码+BrowserRecordingStage9: 规范化根目录；若没有这行代码，后续路径操作不稳定。
        self.base_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+BrowserRecordingStage9: 确保根目录存在；若没有这行代码，首次录制会因目录缺失失败。

    def recording_dir(self, recording_id: str) -> Path:  # 新增代码+BrowserRecordingStage9: 计算某次录制目录；若没有这行代码，manifest 和帧路径容易不一致。
        return self.base_dir / _safe_name(recording_id, "recording")  # 新增代码+BrowserRecordingStage9: 返回安全子目录；若没有这行代码，用户输入可能影响任意路径。

    def manifest_path(self, recording_id: str) -> Path:  # 新增代码+BrowserRecordingStage9: 计算 manifest 路径；若没有这行代码，读写 manifest 会重复拼路径。
        return self.recording_dir(recording_id) / "recording_manifest.json"  # 新增代码+BrowserRecordingStage9: 使用稳定文件名；若没有这行代码，verifier 不知道检查哪个文件。

    def frames_dir(self, recording_id: str) -> Path:  # 新增代码+BrowserRecordingStage9: 计算帧目录；若没有这行代码，帧文件会和 GIF 混在一起。
        return self.recording_dir(recording_id) / "frames"  # 新增代码+BrowserRecordingStage9: 返回 frames 子目录；若没有这行代码，glob 检查无法稳定匹配。

    def _save_manifest(self, manifest: dict[str, Any]) -> Path:  # 新增代码+BrowserRecordingStage9: 原子保存 manifest；若没有这行代码，重复写入细节会散落。
        recording_id = str(manifest.get("recording_id", ""))  # 新增代码+BrowserRecordingStage9: 读取 manifest 自带 id；若没有这行代码，不知道该写哪个目录。
        manifest["updated_at_ms"] = now_ms()  # 新增代码+BrowserRecordingStage9: 保存前刷新更新时间；若没有这行代码，状态页不知道录制是否新鲜。
        manifest["frame_count"] = len(manifest.get("frames", [])) if isinstance(manifest.get("frames", []), list) else 0  # 新增代码+BrowserRecordingStage9: 同步帧数量；若没有这行代码，状态页需要每次自己数。
        return atomic_write_json(self.manifest_path(recording_id), manifest)  # 新增代码+BrowserRecordingStage9: 写入 JSON 并返回路径；若没有这行代码，manifest 不会落盘。

    def load_recording(self, recording_id: str) -> dict[str, Any]:  # 新增代码+BrowserRecordingStage9: 读取指定录制 manifest；若没有这行代码，stop/export/status 无法复用状态。
        payload = read_json_or_default(self.manifest_path(recording_id), None)  # 新增代码+BrowserRecordingStage9: 容错读取 JSON；若没有这行代码，坏 manifest 会直接抛异常。
        if not isinstance(payload, dict):  # 新增代码+BrowserRecordingStage9: 缺失或非对象视为找不到；若没有这行代码，后续字段读取会崩溃。
            raise FileNotFoundError(f"找不到浏览器录制：{recording_id}")  # 新增代码+BrowserRecordingStage9: 抛出清楚错误；若没有这行代码，用户不知道哪个 recording_id 错了。
        return payload  # 新增代码+BrowserRecordingStage9: 返回 manifest 字典；若没有这行代码，调用方拿不到录制状态。

    def start_recording(self, recording_id: str = "", run_id: str = "", page_id: str = "", metadata: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+BrowserRecordingStage9: 开始一次录制；若没有这行代码，工具无法创建视觉证据根对象。
        safe_recording_id = _safe_name(recording_id, f"recording_{now_ms()}_{secrets.token_hex(4)}")  # 新增代码+BrowserRecordingStage9: 生成或清洗录制 id；若没有这行代码，多次录制可能撞名或路径不安全。
        self.frames_dir(safe_recording_id).mkdir(parents=True, exist_ok=True)  # 新增代码+BrowserRecordingStage9: 创建帧目录；若没有这行代码，后续 page.screenshot 无处保存。
        manifest = {  # 新增代码+BrowserRecordingStage9: 构造 manifest 根对象；若没有这行代码，录制状态没有统一结构。
            "schema_version": 1,  # 新增代码+BrowserRecordingStage9: 标记 manifest 结构版本；若没有这行代码，后续升级无法兼容判断。
            "recording_id": safe_recording_id,  # 新增代码+BrowserRecordingStage9: 保存录制 id；若没有这行代码，状态页无法引用录制。
            "run_id": str(run_id or ""),  # 新增代码+BrowserRecordingStage9: 保存关联 browser run；若没有这行代码，录制和动作证据会断链。
            "page_id": str(page_id or ""),  # 新增代码+BrowserRecordingStage9: 保存初始页面 id；若没有这行代码，多标签页录制难以复盘。
            "status": "recording",  # 新增代码+BrowserRecordingStage9: 标记当前正在录制；若没有这行代码，后续动作不知道是否自动捕帧。
            "created_at_ms": now_ms(),  # 新增代码+BrowserRecordingStage9: 保存创建时间；若没有这行代码，多次录制无法排序。
            "updated_at_ms": now_ms(),  # 新增代码+BrowserRecordingStage9: 保存更新时间；若没有这行代码，状态页无法判断新旧。
            "stopped_at_ms": 0,  # 新增代码+BrowserRecordingStage9: 预留停止时间；若没有这行代码，停止后缺少时间线。
            "duration_ms": 0,  # 新增代码+BrowserRecordingStage9: 预留总时长；若没有这行代码，用户不知道录制持续多久。
            "frame_count": 0,  # 新增代码+BrowserRecordingStage9: 初始化帧数量；若没有这行代码，状态页可能显示缺字段。
            "frames": [],  # 新增代码+BrowserRecordingStage9: 初始化帧列表；若没有这行代码，record_frame 无法追加。
            "gif_path": "",  # 新增代码+BrowserRecordingStage9: 初始化 GIF 路径；若没有这行代码，未导出状态不明确。
            "metadata": dict(metadata or {}),  # 新增代码+BrowserRecordingStage9: 保存扩展元数据副本；若没有这行代码，session/provider 等上下文无处存放。
        }  # 新增代码+BrowserRecordingStage9: 结束 manifest 对象；若没有这行代码，Python 字典语法无法闭合。
        self._save_manifest(manifest)  # 新增代码+BrowserRecordingStage9: 立刻落盘 manifest；若没有这行代码，中断后看不到录制已启动。
        return manifest  # 新增代码+BrowserRecordingStage9: 返回录制状态；若没有这行代码，工具无法告诉模型 recording_id。

    def record_frame(self, recording_id: str, frame_path: str | Path, tool_name: str = "", action_id: str = "", page_id: str = "", url: str = "", title: str = "") -> dict[str, Any]:  # 新增代码+BrowserRecordingStage9: 向 manifest 追加一帧；若没有这行代码，PNG 文件无法形成可回放序列。
        manifest = self.load_recording(recording_id)  # 新增代码+BrowserRecordingStage9: 读取当前 manifest；若没有这行代码，追加会覆盖旧帧。
        frames = manifest.get("frames", []) if isinstance(manifest.get("frames", []), list) else []  # 新增代码+BrowserRecordingStage9: 安全读取已有帧；若没有这行代码，坏 manifest 会导致追加失败。
        path = Path(frame_path)  # 新增代码+BrowserRecordingStage9: 规范化帧路径；若没有这行代码，exists 和输出会不稳定。
        frame = {  # 新增代码+BrowserRecordingStage9: 构造单帧元数据；若没有这行代码，帧只有文件没有审计上下文。
            "index": len(frames) + 1,  # 新增代码+BrowserRecordingStage9: 保存帧序号；若没有这行代码，回放顺序只能靠文件名猜。
            "timestamp_ms": now_ms(),  # 新增代码+BrowserRecordingStage9: 保存帧时间；若没有这行代码，动作过程时间线不可见。
            "frame_path": str(path),  # 新增代码+BrowserRecordingStage9: 保存帧文件路径；若没有这行代码，verifier 找不到图片。
            "exists": path.exists(),  # 新增代码+BrowserRecordingStage9: 保存记录时是否存在；若没有这行代码，坏路径不明显。
            "tool_name": str(tool_name or ""),  # 新增代码+BrowserRecordingStage9: 保存触发帧的工具；若没有这行代码，用户不知道画面对应哪一步。
            "action_id": str(action_id or ""),  # 新增代码+BrowserRecordingStage9: 保存关联 action；若没有这行代码，帧和 browser runtime 动作难以互查。
            "page_id": str(page_id or manifest.get("page_id", "")),  # 新增代码+BrowserRecordingStage9: 保存页面 id；若没有这行代码，多页任务难以复盘。
            "url": str(url or ""),  # 新增代码+BrowserRecordingStage9: 保存页面 URL；若没有这行代码，画面来源不清楚。
            "title": str(title or ""),  # 新增代码+BrowserRecordingStage9: 保存页面标题；若没有这行代码，状态摘要不可读。
        }  # 新增代码+BrowserRecordingStage9: 结束帧元数据；若没有这行代码，Python 字典语法无法闭合。
        frames.append(frame)  # 新增代码+BrowserRecordingStage9: 把新帧追加到序列；若没有这行代码，manifest 帧数不会增加。
        manifest["frames"] = frames  # 新增代码+BrowserRecordingStage9: 写回帧列表；若没有这行代码，保存时仍是旧帧。
        self._save_manifest(manifest)  # 新增代码+BrowserRecordingStage9: 保存更新后的 manifest；若没有这行代码，中断后会丢帧。
        return frame  # 新增代码+BrowserRecordingStage9: 返回帧元数据；若没有这行代码，工具无法输出 frame_path。

    def stop_recording(self, recording_id: str) -> dict[str, Any]:  # 新增代码+BrowserRecordingStage9: 停止录制并固化状态；若没有这行代码，录制会一直显示 recording。
        manifest = self.load_recording(recording_id)  # 新增代码+BrowserRecordingStage9: 读取 manifest；若没有这行代码，无法更新状态。
        manifest["status"] = "stopped" if manifest.get("status") != "exported" else "exported"  # 新增代码+BrowserRecordingStage9: 没导出时标记 stopped；若没有这行代码，状态页无法区分仍在录制和已停止。
        manifest["stopped_at_ms"] = now_ms()  # 新增代码+BrowserRecordingStage9: 保存停止时间；若没有这行代码，总时长无法计算。
        manifest["duration_ms"] = max(0, int(manifest["stopped_at_ms"]) - int(manifest.get("created_at_ms", manifest["stopped_at_ms"])))  # 新增代码+BrowserRecordingStage9: 计算录制时长；若没有这行代码，性能和过程审计缺少时间。
        self._save_manifest(manifest)  # 新增代码+BrowserRecordingStage9: 保存停止状态；若没有这行代码，重启后状态仍像运行中。
        return manifest  # 新增代码+BrowserRecordingStage9: 返回停止后的 manifest；若没有这行代码，工具无法输出帧数。

    def export_gif(self, recording_id: str, output_name: str = "", duration_ms: int = 700) -> dict[str, Any]:  # 新增代码+BrowserRecordingStage9: 把帧序列导出为 GIF；若没有这行代码，用户只能逐张看图。
        manifest = self.load_recording(recording_id)  # 新增代码+BrowserRecordingStage9: 读取 manifest；若没有这行代码，导出不知道帧列表。
        frames = manifest.get("frames", []) if isinstance(manifest.get("frames", []), list) else []  # 新增代码+BrowserRecordingStage9: 安全读取帧列表；若没有这行代码，坏 manifest 会崩溃。
        frame_paths = [Path(frame.get("frame_path", "")) for frame in frames if isinstance(frame, dict) and Path(frame.get("frame_path", "")).exists()]  # 新增代码+BrowserRecordingStage9: 只导出真实存在的帧；若没有这行代码，缺帧会让 Pillow 报难懂错误。
        if not frame_paths:  # 新增代码+BrowserRecordingStage9: 拒绝空帧导出；若没有这行代码，会生成假成功或空 GIF。
            raise RuntimeError(f"录制 {recording_id} 没有可导出的帧。")  # 新增代码+BrowserRecordingStage9: 返回中文错误；若没有这行代码，用户不知道需要先截图/操作。
        safe_output = _safe_name(output_name, f"{manifest.get('recording_id', recording_id)}.gif")  # 新增代码+BrowserRecordingStage9: 清洗输出文件名；若没有这行代码，output_name 可能逃出目录。
        if not safe_output.lower().endswith(".gif"):  # 新增代码+BrowserRecordingStage9: 检查后缀；若没有这行代码，用户可能生成无扩展名文件。
            safe_output = f"{safe_output}.gif"  # 新增代码+BrowserRecordingStage9: 自动补 GIF 后缀；若没有这行代码，肉眼查找文件不方便。
        gif_path = self.recording_dir(str(manifest.get("recording_id", recording_id))) / safe_output  # 新增代码+BrowserRecordingStage9: 计算 GIF 输出路径；若没有这行代码，导出位置不稳定。
        images = [Image.open(path).convert("RGB") for path in frame_paths]  # 新增代码+BrowserRecordingStage9: 打开并统一帧格式；若没有这行代码，透明 PNG 或模式差异可能导出失败。
        try:  # 新增代码+BrowserRecordingStage9: 确保导出后关闭图片资源；若没有这行代码，Windows 上文件可能被占用。
            first, rest = images[0], images[1:]  # 新增代码+BrowserRecordingStage9: Pillow 需要第一帧和追加帧分开；若没有这行代码，save 调用不清晰。
            first.save(gif_path, save_all=True, append_images=rest, duration=max(50, int(duration_ms)), loop=0)  # 新增代码+BrowserRecordingStage9: 写出真实 GIF；若没有这行代码，Stage 9 没有可视化过程 artifact。
        finally:  # 新增代码+BrowserRecordingStage9: 无论导出成功失败都关闭资源；若没有这行代码，图片句柄会泄漏。
            for image in images:  # 新增代码+BrowserRecordingStage9: 遍历所有打开的图片；若没有这行代码，只会关闭第一张。
                image.close()  # 新增代码+BrowserRecordingStage9: 关闭图片文件句柄；若没有这行代码，测试清理目录可能失败。
        manifest["status"] = "exported"  # 新增代码+BrowserRecordingStage9: 标记已导出；若没有这行代码，状态页不知道 GIF 是否生成。
        manifest["gif_path"] = str(gif_path)  # 新增代码+BrowserRecordingStage9: 保存 GIF 路径；若没有这行代码，UI/verifier 找不到产物。
        manifest["gif_exists"] = gif_path.exists()  # 新增代码+BrowserRecordingStage9: 保存 GIF 存在状态；若没有这行代码，状态页可能显示假路径。
        self._save_manifest(manifest)  # 新增代码+BrowserRecordingStage9: 保存导出状态；若没有这行代码，重启后 GIF 证据丢失。
        return manifest  # 新增代码+BrowserRecordingStage9: 返回导出后的 manifest；若没有这行代码，工具无法输出 gif_path。

    def list_recordings(self, limit: int = 20) -> list[dict[str, Any]]:  # 新增代码+BrowserRecordingStage9: 列出最近录制；若没有这行代码，状态快照无法展示视觉证据。
        manifests: list[dict[str, Any]] = []  # 新增代码+BrowserRecordingStage9: 准备收集 manifest；若没有这行代码，函数没有返回容器。
        if not self.base_dir.exists():  # 新增代码+BrowserRecordingStage9: 首次运行无目录时返回空列表；若没有这行代码，状态页会报错。
            return []  # 新增代码+BrowserRecordingStage9: 返回空录制列表；若没有这行代码，调用方要自己兜底。
        for manifest_file in self.base_dir.glob("*/recording_manifest.json"):  # 新增代码+BrowserRecordingStage9: 扫描所有录制 manifest；若没有这行代码，状态页看不到历史录制。
            payload = read_json_or_default(manifest_file, None)  # 新增代码+BrowserRecordingStage9: 容错读取 manifest；若没有这行代码，一个坏文件会拖垮全部状态。
            if isinstance(payload, dict):  # 新增代码+BrowserRecordingStage9: 只接受对象 manifest；若没有这行代码，非对象会污染输出。
                manifests.append(payload)  # 新增代码+BrowserRecordingStage9: 加入结果列表；若没有这行代码，扫描结果会为空。
        manifests.sort(key=lambda item: int(item.get("updated_at_ms", 0)), reverse=True)  # 新增代码+BrowserRecordingStage9: 按更新时间倒序；若没有这行代码，latest 可能不是最新录制。
        return manifests[:limit] if limit > 0 else manifests  # 新增代码+BrowserRecordingStage9: 返回限制数量或全量；若没有这行代码，状态输出可能过大。


def run_recording_selftest(workspace: str | Path) -> dict[str, Any]:  # 新增代码+BrowserRecordingStage9: 生成真实帧和 GIF 自测产物；若没有这行代码，真实终端验收无法给 verifier 留可查 artifact。
    root = Path(workspace)  # 新增代码+BrowserRecordingStage9: 规范化工作区；若没有这行代码，字符串路径无法稳定拼接。
    store = BrowserRecordingStore(root / "browser_artifacts" / "browser_recordings")  # 新增代码+BrowserRecordingStage9: 使用生产 artifact 目录；若没有这行代码，verifier 的 project_root glob 找不到产物。
    recording_id = f"stage9_selftest_{now_ms()}_{secrets.token_hex(3)}"  # 新增代码+BrowserRecordingStage9: 创建唯一自测录制 id；若没有这行代码，多次验收会互相覆盖。
    store.start_recording(recording_id=recording_id, run_id="stage9_selftest", page_id="selftest")  # 新增代码+BrowserRecordingStage9: 写入自测 manifest；若没有这行代码，产物没有录制根。
    colors = [(200, 40, 40), (40, 140, 220), (40, 180, 90)]  # 新增代码+BrowserRecordingStage9: 准备三帧颜色；若没有这行代码，GIF 过程证据不明显。
    for index, color in enumerate(colors, start=1):  # 新增代码+BrowserRecordingStage9: 逐帧生成测试图片；若没有这行代码，自测没有帧序列。
        frame_path = store.frames_dir(recording_id) / f"frame-{index:04d}.png"  # 新增代码+BrowserRecordingStage9: 计算帧文件路径；若没有这行代码，帧命名不稳定。
        Image.new("RGB", (64, 40), color).save(frame_path)  # 新增代码+BrowserRecordingStage9: 保存真实 PNG 帧；若没有这行代码，GIF 导出没有输入。
        store.record_frame(recording_id, frame_path, tool_name=f"selftest_frame_{index}", action_id=f"selftest-action-{index}", page_id="selftest", url="about:stage9-selftest", title="Stage 9 Selftest")  # 新增代码+BrowserRecordingStage9: 记录帧元数据；若没有这行代码，manifest 不知道图片属于哪一步。
    store.stop_recording(recording_id)  # 新增代码+BrowserRecordingStage9: 停止自测录制；若没有这行代码，manifest 状态仍是 recording。
    return store.export_gif(recording_id, output_name="stage9_selftest.gif", duration_ms=180)  # 新增代码+BrowserRecordingStage9: 导出自测 GIF 并返回 manifest；若没有这行代码，verifier 没有 GIF artifact 可查。


def main(argv: list[str] | None = None) -> int:  # 新增代码+BrowserRecordingStage9: 提供命令行入口；若没有这行代码，`python -m` 不能用于真实终端验收。
    parser = argparse.ArgumentParser(description="LearningAgent browser recording utilities")  # 新增代码+BrowserRecordingStage9: 创建参数解析器；若没有这行代码，命令行参数无说明。
    parser.add_argument("--selftest", action="store_true", help="create a real Stage 9 recording selftest artifact")  # 新增代码+BrowserRecordingStage9: 添加自测开关；若没有这行代码，验收命令不知道执行什么。
    parser.add_argument("--workspace", default=".", help="workspace root for browser_artifacts")  # 新增代码+BrowserRecordingStage9: 添加工作区参数；若没有这行代码，自测产物可能写错目录。
    args = parser.parse_args(argv)  # 新增代码+BrowserRecordingStage9: 解析命令行参数；若没有这行代码，函数拿不到用户输入。
    if args.selftest:  # 新增代码+BrowserRecordingStage9: 只有传自测开关才创建产物；若没有这行代码，运行模块会无条件写文件。
        manifest = run_recording_selftest(args.workspace)  # 新增代码+BrowserRecordingStage9: 执行真实帧/GIF 自测；若没有这行代码，命令行没有核心行为。
        print("STAGE9_RECORDING_SELFTEST_OK")  # 新增代码+BrowserRecordingStage9: 输出稳定成功标记；若没有这行代码，验收日志不易匹配。
        print(f"recording_id={manifest.get('recording_id', '')}")  # 新增代码+BrowserRecordingStage9: 输出录制 id；若没有这行代码，用户无法定位产物目录。
        print(f"frame_count={manifest.get('frame_count', 0)}")  # 新增代码+BrowserRecordingStage9: 输出帧数；若没有这行代码，用户不知道证据是否有内容。
        print(f"gif_path={manifest.get('gif_path', '')}")  # 新增代码+BrowserRecordingStage9: 输出 GIF 路径；若没有这行代码，用户无法打开视觉证据。
        return 0  # 新增代码+BrowserRecordingStage9: 自测成功返回 0；若没有这行代码，shell 无法判断成功。
    parser.print_help()  # 新增代码+BrowserRecordingStage9: 未指定动作时显示帮助；若没有这行代码，用户会看到空输出。
    return 2  # 新增代码+BrowserRecordingStage9: 未指定动作返回非零；若没有这行代码，误调用会被当作成功。


if __name__ == "__main__":  # 新增代码+BrowserRecordingStage9: 支持 `python -m learning_agent.browser.recording`；若没有这行代码，命令行入口不会执行。
    raise SystemExit(main())  # 新增代码+BrowserRecordingStage9: 用 main 返回码退出；若没有这行代码，脚本成功/失败状态不稳定。
