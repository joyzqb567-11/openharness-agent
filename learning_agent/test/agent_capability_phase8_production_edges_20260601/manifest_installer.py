"""Chrome native host manifest 生成器。"""  # 新增代码+ChromeExtensionStage5: 说明本文件只生成 manifest，不写注册表；若没有这行代码，用户可能担心系统副作用。
from __future__ import annotations  # 新增代码+ChromeExtensionStage5: 延迟解析类型注解；若没有这行代码，Path 标注更脆弱。

import json  # 新增代码+ChromeExtensionStage5: 写 manifest JSON；若没有这行代码，安装文件无法生成。
import sys  # 新增代码+Phase1Installer: 判断当前平台是否支持 Windows registry；如果没有这行代码，非 Windows 环境会误报可注册。
from pathlib import Path  # 新增代码+ChromeExtensionStage5: 处理输出路径；若没有这行代码，路径拼接不稳定。
from typing import Protocol  # 新增代码+Phase1Installer: 定义注册表适配器协议；如果没有这行代码，安装器无法安全替换真实 registry 和测试 fake registry。


NATIVE_HOST_NAME = "com.openharness.learning_agent"  # 新增代码+Phase1Installer: 固定 Chrome native host 名称；如果没有这行代码，manifest 名称和 registry key 可能不一致。
WINDOWS_NATIVE_HOST_REGISTRY_PATH = rf"Software\Google\Chrome\NativeMessagingHosts\{NATIVE_HOST_NAME}"  # 新增代码+Phase1Installer: 固定 Chrome 在 HKCU 下查找 native host 的 registry 路径；如果没有这行代码，安装器不知道写到哪里。
WINDOWS_NATIVE_HOST_REGISTRY_PATHS = [rf"Software\Google\Chrome\NativeMessagingHosts\{NATIVE_HOST_NAME}", rf"Software\Microsoft\Edge\NativeMessagingHosts\{NATIVE_HOST_NAME}", rf"Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\{NATIVE_HOST_NAME}", rf"Software\Chromium\NativeMessagingHosts\{NATIVE_HOST_NAME}"]  # 新增代码+Phase8ProductionEdges: 覆盖 Chrome/Edge/Brave/Chromium 等常见浏览器注册位置；如果没有这行代码，native host 仍停留在单 Chrome key。


class NativeHostRegistryAdapter(Protocol):  # 新增代码+Phase1Installer: 定义 registry 读写协议；如果没有这个协议，真实注册表和 fake 注册表会耦合在一起。
    def read_value(self, key_path: str) -> str:  # 新增代码+Phase1Installer: 读取 registry value；如果没有这行代码，status 无法判断 native host 是否已注册。
        ...  # 新增代码+Phase1Installer: Protocol 方法占位；如果没有这行代码，类型检查器不知道实现类需要返回字符串。

    def write_value(self, key_path: str, value: str) -> None:  # 新增代码+Phase1Installer: 写入 registry value；如果没有这行代码，install 无法注册 native host。
        ...  # 新增代码+Phase1Installer: Protocol 方法占位；如果没有这行代码，fake 和真实适配器接口不统一。

    def delete_value(self, key_path: str) -> None:  # 新增代码+Phase1Installer: 删除 registry value；如果没有这行代码，uninstall 无法回滚注册。
        ...  # 新增代码+Phase1Installer: Protocol 方法占位；如果没有这行代码，卸载接口没有统一约束。


class MemoryNativeHostRegistryAdapter:  # 新增代码+Phase1Installer: 提供内存 registry 适配器；如果没有这个类，测试只能碰真实 Windows registry。
    def __init__(self) -> None:  # 新增代码+Phase1Installer: 初始化内存表；如果没有这行代码，每个测试无法拥有独立 registry 状态。
        self.values: dict[str, str] = {}  # 新增代码+Phase1Installer: 保存 key_path 到 manifest 路径的映射；如果没有这行代码，fake registry 没有存储位置。

    def read_value(self, key_path: str) -> str:  # 新增代码+Phase1Installer: 从内存读取 registry value；如果没有这行代码，status 测试无法检查注册状态。
        return self.values.get(str(key_path or ""), "")  # 新增代码+Phase1Installer: 找不到时返回空字符串；如果没有这行代码，未注册状态会抛异常。

    def write_value(self, key_path: str, value: str) -> None:  # 新增代码+Phase1Installer: 写入内存 registry；如果没有这行代码，install 测试无法模拟注册成功。
        self.values[str(key_path or "")] = str(value or "")  # 新增代码+Phase1Installer: 保存规范化字符串；如果没有这行代码，Path 对象可能污染 fake 状态。

    def delete_value(self, key_path: str) -> None:  # 新增代码+Phase1Installer: 删除内存 registry value；如果没有这行代码，uninstall 测试无法模拟回滚。
        self.values.pop(str(key_path or ""), None)  # 新增代码+Phase1Installer: 不存在时静默成功；如果没有这行代码，重复卸载会抛无意义异常。


class WindowsNativeHostRegistryAdapter:  # 新增代码+Phase1Installer: 封装真实 Windows registry；如果没有这个类，生产安装无法写入 Chrome native host 注册位置。
    def __init__(self, root_name: str = "HKEY_CURRENT_USER") -> None:  # 新增代码+Phase1Installer: 允许未来扩展 registry 根；如果没有这行代码，测试和生产根路径无法表达。
        self.root_name = str(root_name or "HKEY_CURRENT_USER")  # 新增代码+Phase1Installer: 保存根路径名称；如果没有这行代码，审计记录无法说明写入范围。

    def _winreg(self):  # 新增代码+Phase1Installer: 延迟导入 winreg；如果没有这行代码，非 Windows 环境导入模块会失败。
        if sys.platform != "win32":  # 新增代码+Phase1Installer: 非 Windows 平台拒绝真实 registry；如果没有这行代码，Linux/macOS 会得到误导性错误。
            raise RuntimeError("真实 Windows registry 只允许在 Windows 平台使用。")  # 新增代码+Phase1Installer: 明确平台限制；如果没有这行代码，用户不知道为什么不能安装。
        import winreg  # type: ignore  # 新增代码+Phase1Installer: 导入 Windows registry API；如果没有这行代码，真实适配器无法工作。
        return winreg  # 新增代码+Phase1Installer: 返回模块给调用方；如果没有这行代码，后续方法拿不到 API。

    def _root(self):  # 新增代码+Phase1Installer: 解析 registry 根；如果没有这行代码，读写方法会重复判断根路径。
        winreg = self._winreg()  # 新增代码+Phase1Installer: 获取 winreg 模块；如果没有这行代码，无法访问 HKEY 常量。
        if self.root_name != "HKEY_CURRENT_USER":  # 新增代码+Phase1Installer: 当前只支持 HKCU，避免误写系统级 HKLM；如果没有这行代码，权限边界不清楚。
            raise RuntimeError("当前安装器只支持 HKEY_CURRENT_USER，避免误写系统级注册表。")  # 新增代码+Phase1Installer: 明确拒绝系统级写入；如果没有这行代码，可能需要管理员权限并影响全局系统。
        return winreg.HKEY_CURRENT_USER  # 新增代码+Phase1Installer: 返回 HKCU 常量；如果没有这行代码，读写没有根句柄。

    def read_value(self, key_path: str) -> str:  # 新增代码+Phase1Installer: 读取真实 registry 默认值；如果没有这行代码，status 不能检查生产安装。
        winreg = self._winreg()  # 新增代码+Phase1Installer: 获取 winreg；如果没有这行代码，无法调用 OpenKey。
        try:  # 新增代码+Phase1Installer: registry key 可能不存在；如果没有这行代码，未安装状态会抛异常。
            with winreg.OpenKey(self._root(), key_path) as key:  # 新增代码+Phase1Installer: 打开 HKCU native host key；如果没有这行代码，无法读取默认值。
                value, _kind = winreg.QueryValueEx(key, None)  # 新增代码+Phase1Installer: 读取默认值；如果没有这行代码，不知道 Chrome 指向哪个 manifest。
                return str(value or "")  # 新增代码+Phase1Installer: 返回字符串值；如果没有这行代码，Path 比较不稳定。
        except FileNotFoundError:  # 新增代码+Phase1Installer: key 不存在表示未注册；如果没有这行代码，status 会把正常未安装当错误。
            return ""  # 新增代码+Phase1Installer: 未注册返回空；如果没有这行代码，调用方需要捕获异常。

    def write_value(self, key_path: str, value: str) -> None:  # 新增代码+Phase1Installer: 写入真实 registry 默认值；如果没有这行代码，生产安装无法让 Chrome 找到 manifest。
        winreg = self._winreg()  # 新增代码+Phase1Installer: 获取 winreg；如果没有这行代码，无法创建 key。
        with winreg.CreateKey(self._root(), key_path) as key:  # 新增代码+Phase1Installer: 创建或打开 HKCU key；如果没有这行代码，默认值无处写入。
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, str(value or ""))  # 新增代码+Phase1Installer: 写入 manifest 路径；如果没有这行代码，Chrome native messaging 不会生效。

    def delete_value(self, key_path: str) -> None:  # 新增代码+Phase1Installer: 删除真实 registry key；如果没有这行代码，卸载后 Chrome 仍会尝试启动旧 host。
        winreg = self._winreg()  # 新增代码+Phase1Installer: 获取 winreg；如果没有这行代码，无法删除 key。
        try:  # 新增代码+Phase1Installer: key 可能已经不存在；如果没有这行代码，重复卸载会失败。
            winreg.DeleteKey(self._root(), key_path)  # 新增代码+Phase1Installer: 删除 HKCU native host key；如果没有这行代码，注册项会残留。
        except FileNotFoundError:  # 新增代码+Phase1Installer: 未注册时卸载应视为安全完成；如果没有这行代码，卸载不幂等。
            return  # 新增代码+Phase1Installer: key 不存在直接返回；如果没有这行代码，用户会看到无意义错误。


def build_native_host_launcher(target_dir: Path, python_executable: str, host_script: Path) -> Path:  # 新增代码+Phase8ProductionEdges: 生成可被 manifest 直接指向的 Windows launcher；如果没有这段函数，Chrome 可能尝试直接执行不能携带解释器参数的裸 Python 脚本。
    safe_target_dir = Path(target_dir)  # 新增代码+Phase8ProductionEdges: 规范 launcher 输出目录；如果没有这行代码，字符串路径和 Path 路径行为不统一。
    safe_target_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+Phase8ProductionEdges: 确保 launcher 目录存在；如果没有这行代码，首次安装会因为目录缺失而失败。
    launcher_path = safe_target_dir / f"{NATIVE_HOST_NAME}.cmd"  # 新增代码+Phase8ProductionEdges: 固定 launcher 文件名；如果没有这行代码，manifest 和排障信息无法稳定指向同一入口。
    launcher_text = f'@echo off\r\n"{python_executable or "python"}" "{Path(host_script)}"\r\n'  # 新增代码+Phase8ProductionEdges: 用 cmd 启动 Python host 脚本；如果没有这行代码，native host 没有真正可执行的转发入口。
    launcher_path.write_text(launcher_text, encoding="utf-8")  # 新增代码+Phase8ProductionEdges: 把 launcher 写入磁盘；如果没有这行代码，manifest 会指向不存在的文件。
    return launcher_path  # 新增代码+Phase8ProductionEdges: 返回 launcher 路径；如果没有这行代码，manifest 构建函数拿不到可执行入口。


def build_native_host_manifest(target_dir: Path, extension_id: str, python_executable: str, host_script: Path) -> Path:  # 新增代码+ChromeExtensionStage5: 生成 native host manifest 文件；若没有这行代码，插件无法知道本地 host 入口。
    safe_target_dir = Path(target_dir)  # 新增代码+ChromeExtensionStage5: 规范输出目录；若没有这行代码，调用方传字符串时不稳定。
    safe_target_dir.mkdir(parents=True, exist_ok=True)  # 新增代码+ChromeExtensionStage5: 确保输出目录存在；若没有这行代码，首次生成会失败。
    safe_extension_id = str(extension_id or "").strip()  # 新增代码+ChromeExtensionStage5: 清理扩展 id；若没有这行代码，allowed_origins 可能带空格。
    launcher_path = build_native_host_launcher(safe_target_dir, python_executable, host_script)  # 新增代码+Phase8ProductionEdges: 先生成 launcher 再写 manifest；如果没有这行代码，manifest 仍会指向裸脚本。
    manifest = {"name": NATIVE_HOST_NAME, "description": "OpenHarness learning_agent Chrome bridge native host", "path": str(launcher_path), "type": "stdio", "allowed_origins": [f"chrome-extension://{safe_extension_id}/"], "metadata": {"python_executable": str(python_executable or "python"), "host_script": str(Path(host_script))}}  # 修改代码+Phase8ProductionEdges: manifest 指向 launcher 并保留脚本元数据；如果没有这行代码，真实 Chrome native messaging 启动链路不够生产化。
    manifest_path = safe_target_dir / f"{NATIVE_HOST_NAME}.json"  # 修改代码+Phase1Installer: manifest 文件名跟 host 名称一致；如果没有这行代码，用户可能安装错误文件。
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")  # 新增代码+ChromeExtensionStage5: 写入 UTF-8 JSON；若没有这行代码，manifest 不会落盘。
    return manifest_path  # 新增代码+ChromeExtensionStage5: 返回生成路径；若没有这行代码，调用方无法展示或测试文件。


class ChromeNativeHostInstaller:  # 新增代码+Phase1Installer: 管理 Chrome native host 安装生命周期；如果没有这个类，Phase 1 只能生成 manifest，不能检测或回滚安装。
    def __init__(self, target_dir: Path, registry_adapter: NativeHostRegistryAdapter | None = None, registry_key_path: str = WINDOWS_NATIVE_HOST_REGISTRY_PATH, registry_key_paths: list[str] | None = None) -> None:  # 修改代码+Phase8ProductionEdges: 初始化安装目录、主 registry key 和多浏览器 registry key；如果没有这行代码，安装器只能管理单个 Chrome 注册位置。
        self.target_dir = Path(target_dir)  # 新增代码+Phase1Installer: 保存 manifest 输出目录；如果没有这行代码，安装器不知道文件写到哪里。
        self.registry_adapter = registry_adapter or WindowsNativeHostRegistryAdapter()  # 新增代码+Phase1Installer: 默认使用真实 Windows 适配器；如果没有这行代码，生产路径无法注册。
        self.registry_key_path = str(registry_key_path or WINDOWS_NATIVE_HOST_REGISTRY_PATH)  # 新增代码+Phase1Installer: 保存 registry key；如果没有这行代码，状态和安装会使用不同位置。
        self.registry_key_paths = [str(path) for path in (registry_key_paths or WINDOWS_NATIVE_HOST_REGISTRY_PATHS)]  # 新增代码+Phase8ProductionEdges: 保存所有要注册的浏览器 key；如果没有这行代码，install/uninstall 无法覆盖 Edge/Brave/Chromium。
        self.last_action = ""  # 新增代码+Phase1Installer: 记录当前安装器实例最近动作；如果没有这行代码，dry-run 生成 manifest 和卸载后 registry 缺失无法区分提示。

    def manifest_path(self) -> Path:  # 新增代码+Phase1Installer: 返回固定 manifest 路径；如果没有这行代码，多处路径拼接可能不一致。
        return self.target_dir / f"{NATIVE_HOST_NAME}.json"  # 新增代码+Phase1Installer: 使用 host 名称拼 manifest 文件；如果没有这行代码，状态找不到 install 生成的文件。

    def _registry_value(self) -> str:  # 新增代码+Phase1Installer: 安全读取 registry 当前值；如果没有这行代码，status/install 会重复异常处理。
        try:  # 新增代码+Phase1Installer: registry adapter 可能因平台或权限失败；如果没有这行代码，状态工具会直接崩溃。
            return str(self.registry_adapter.read_value(self.registry_key_path) or "")  # 新增代码+Phase1Installer: 读取并规范化 registry 值；如果没有这行代码，None 会污染状态。
        except Exception as error:  # 新增代码+Phase1Installer: 把底层错误转成可展示状态；如果没有这行代码，小白用户只会看到堆栈。
            return f"ERROR:{error}"  # 新增代码+Phase1Installer: 用前缀保存错误；如果没有这行代码，调用方无法区分空值和读取失败。

    def status(self) -> dict[str, object]:  # 新增代码+Phase1Installer: 输出安装状态；如果没有这行代码，agent 无法判断下一步该生成 manifest 还是写 registry。
        manifest_path = self.manifest_path()  # 新增代码+Phase1Installer: 读取预期 manifest 路径；如果没有这行代码，状态没有文件证据。
        manifest_exists = manifest_path.exists()  # 新增代码+Phase1Installer: 判断 manifest 是否存在；如果没有这行代码，状态无法区分未生成和已生成。
        registry_value = self._registry_value()  # 新增代码+Phase1Installer: 读取 registry 当前值；如果没有这行代码，状态不知道是否注册。
        if registry_value.startswith("ERROR:"):  # 新增代码+Phase1Installer: registry 读取失败单独报告；如果没有这行代码，权限错误可能被误判未安装。
            state = "registry_unavailable"  # 新增代码+Phase1Installer: 设置 registry 不可用状态；如果没有这行代码，repair hint 无法给出正确建议。
        elif registry_value and Path(registry_value) == manifest_path:  # 新增代码+Phase1Installer: registry 指向当前 manifest 才算已注册；如果没有这行代码，旧路径也会被误报成功。
            state = "registry_registered"  # 新增代码+Phase1Installer: 设置已注册状态；如果没有这行代码，安装成功无法被识别。
        elif manifest_exists and registry_value:  # 新增代码+Phase1Installer: manifest 存在但 registry 指向别处；如果没有这行代码，错误路径不容易发现。
            state = "registry_mismatch"  # 新增代码+Phase1Installer: 设置不匹配状态；如果没有这行代码，用户不知道 Chrome 会找错文件。
        elif manifest_exists and self.last_action == "uninstall":  # 新增代码+Phase1Installer: 卸载后 manifest 还在但 registry 缺失；如果没有这行代码，卸载结果会被误报成普通 manifest_created。
            state = "registry_missing"  # 新增代码+Phase1Installer: 设置 registry 缺失状态；如果没有这行代码，用户不知道需要重新注册。
        elif manifest_exists:  # 新增代码+Phase1Installer: manifest 存在但 registry 缺失；如果没有这行代码，dry-run 后状态不明确。
            state = "manifest_created"  # 新增代码+Phase1Installer: 设置已生成 manifest 状态；如果没有这行代码，下一步建议无法精准。
        else:  # 新增代码+Phase1Installer: manifest 和 registry 都没有；如果没有这行代码，初始状态没有兜底。
            state = "not_installed"  # 新增代码+Phase1Installer: 设置未安装状态；如果没有这行代码，首次使用没有清楚提示。
        return {"state": state, "host_name": NATIVE_HOST_NAME, "manifest_path": str(manifest_path), "manifest_exists": manifest_exists, "registry_key_path": self.registry_key_path, "registry_value": registry_value, "registry_targets": list(self.registry_key_paths)}  # 修改代码+Phase8ProductionEdges: 返回机器可读状态和多浏览器目标；如果没有这行代码，/chrome 无法说明安装覆盖范围。

    def install(self, extension_id: str, python_executable: str, host_script: Path, dry_run: bool = True) -> dict[str, object]:  # 新增代码+Phase1Installer: 安装或 dry-run 安装 native host；如果没有这行代码，用户无法从 agent 完成注册准备。
        manifest_path = build_native_host_manifest(self.target_dir, extension_id, python_executable, host_script)  # 新增代码+Phase1Installer: 先生成 manifest；如果没有这行代码，registry 会指向不存在文件。
        audit = {"action": "install", "dry_run": bool(dry_run), "host_name": NATIVE_HOST_NAME, "manifest_path": str(manifest_path), "registry_key_path": self.registry_key_path, "registry_key_paths": list(self.registry_key_paths), "registry_value": str(manifest_path)}  # 修改代码+Phase8ProductionEdges: 构造包含多浏览器 key 的审计记录；如果没有这行代码，用户无法确认本次会写哪些位置。
        if not dry_run:  # 新增代码+Phase1Installer: 只有明确关闭 dry-run 才写 registry；如果没有这行代码，默认可能误改用户系统。
            for key_path in self.registry_key_paths:  # 新增代码+Phase8ProductionEdges: 逐个写入 Chromium 家族 registry key；如果没有这行代码，只有 Chrome 能找到 native host。
                self.registry_adapter.write_value(key_path, str(manifest_path))  # 新增代码+Phase8ProductionEdges: 写入当前浏览器 registry key；如果没有这行代码，对应浏览器不会发现 native host。
        self.last_action = "install"  # 新增代码+Phase1Installer: 记录最近执行安装；如果没有这行代码，后续状态无法解释刚发生的流程。
        return audit  # 新增代码+Phase1Installer: 返回审计记录；如果没有这行代码，调用方不知道安装做了什么。

    def uninstall(self, dry_run: bool = True) -> dict[str, object]:  # 新增代码+Phase1Installer: 卸载或 dry-run 卸载 registry 项；如果没有这行代码，用户无法回滚 native host 注册。
        registry_value_before = self._registry_value()  # 新增代码+Phase1Installer: 记录卸载前 registry 值；如果没有这行代码，审计记录缺少回滚证据。
        audit = {"action": "uninstall", "dry_run": bool(dry_run), "host_name": NATIVE_HOST_NAME, "registry_key_path": self.registry_key_path, "registry_key_paths": list(self.registry_key_paths), "registry_value_before": registry_value_before}  # 修改代码+Phase8ProductionEdges: 构造包含多浏览器 key 的卸载审计；如果没有这行代码，用户不知道会回滚哪些注册项。
        if not dry_run:  # 新增代码+Phase1Installer: 只有明确关闭 dry-run 才删除 registry；如果没有这行代码，状态查询可能误删配置。
            for key_path in self.registry_key_paths:  # 新增代码+Phase8ProductionEdges: 逐个删除 Chromium 家族 registry key；如果没有这行代码，卸载可能只清理 Chrome 而留下 Edge/Brave 残留项。
                self.registry_adapter.delete_value(key_path)  # 新增代码+Phase8ProductionEdges: 删除当前浏览器 registry key；如果没有这行代码，对应浏览器仍会尝试启动旧 host。
        self.last_action = "uninstall"  # 新增代码+Phase1Installer: 记录最近执行卸载；如果没有这行代码，状态无法区分卸载后的 registry 缺失。
        return audit  # 新增代码+Phase1Installer: 返回卸载记录；如果没有这行代码，调用方无法展示结果。

    def repair_hint(self) -> str:  # 新增代码+Phase1Installer: 根据状态生成中文修复建议；如果没有这行代码，小白用户只能看到状态码。
        status = self.status()  # 新增代码+Phase1Installer: 获取当前状态；如果没有这行代码，修复建议没有依据。
        state = str(status.get("state", ""))  # 新增代码+Phase1Installer: 读取状态码；如果没有这行代码，后续分支无法判断。
        if state == "not_installed":  # 新增代码+Phase1Installer: 未安装时提示先生成 manifest；如果没有这行代码，首次使用没有起点。
            return "native host manifest 尚未生成。请先调用 browser_extension_install，默认 dry_run=true 可安全预览，不会写 Windows registry。"  # 新增代码+Phase1Installer: 返回首次安装建议；如果没有这行代码，用户不知道下一步。
        if state == "manifest_created":  # 新增代码+Phase1Installer: 已生成 manifest 但未注册时提示写 registry；如果没有这行代码，用户会停在半安装状态。
            return "native host manifest 已生成，但 Windows registry 尚未注册。确认无误后可用 browser_extension_install 并设置 dry_run=false 完成注册。"  # 新增代码+Phase1Installer: 返回注册建议；如果没有这行代码，Chrome 仍无法连接 host。
        if state == "registry_registered":  # 新增代码+Phase1Installer: 已注册时提示检查配对；如果没有这行代码，用户不知道下一步是 extension pairing。
            return "native host 已注册。下一步请检查 Chrome extension 配对和 session sync 状态。"  # 新增代码+Phase1Installer: 返回后续建议；如果没有这行代码，流程无法衔接 Phase 2。
        if state == "registry_mismatch":  # 新增代码+Phase1Installer: registry 指向旧路径时提示重装；如果没有这行代码，Chrome 会启动错误 host。
            return "Windows registry 指向的 manifest 路径和当前文件不一致。请重新运行 browser_extension_install dry_run=false 或先卸载旧注册项。"  # 新增代码+Phase1Installer: 返回不匹配修复建议；如果没有这行代码，用户不知道为何连接失败。
        return f"native host registry 当前不可用或状态异常：{state}。请检查权限、平台是否为 Windows，并查看 registry_key_path。"  # 新增代码+Phase1Installer: 返回兜底建议；如果没有这行代码，异常状态没有解释。
