"""runtime 与 harness 共用的安全文件写入工具。"""  # 修改代码+RuntimeFileSafetyFallback: 说明本文件负责锁和状态落盘；若没有这行代码，文件写入安全逻辑会散落到各模块。
from __future__ import annotations  # 修改代码+RuntimeFileSafetyFallback: 延迟解析类型注解；若没有这行代码，Path 等类型引用在旧解释顺序下更脆弱。
import json  # 修改代码+RuntimeFileSafetyFallback: 读写 JSON 状态文件需要标准库 json；若没有这行代码，状态只能用脆弱字符串拼接。
import os  # 修改代码+RuntimeFileSafetyFallback: 文件锁、进程号、replace 和底层 fd 操作都需要 os；若没有这行代码，多进程保护无法实现。
import secrets  # 修改代码+RuntimeFileSafetyFallback: 临时文件名需要随机后缀避免并发冲突；若没有这行代码，两个写入可能使用同一个临时文件。
import time  # 修改代码+RuntimeFileSafetyFallback: 锁等待、退避重试和坏文件时间戳需要当前时间；若没有这行代码，等待和审计没有可靠时间来源。
from pathlib import Path  # 修改代码+RuntimeFileSafetyFallback: 用 Path 管理跨平台路径；若没有这行代码，Windows 路径拼接更容易出错。
from typing import Any  # 修改代码+RuntimeFileSafetyFallback: JSON payload 是通用类型；若没有这行代码，函数类型边界不清晰。

try:  # 修改代码+RuntimeFileSafetyFallback: 尝试导入 Windows 字节锁模块；若没有这行代码，Windows 下只能依赖会被删除权限卡住的锁文件。
    import msvcrt  # type: ignore[import-not-found]  # 新增代码+RuntimeFileSafetyFallback: 引入 Windows 原生字节锁能力；若没有这行代码，锁文件删不掉时 FileLock 会永久卡住。
except ImportError:  # 修改代码+RuntimeFileSafetyFallback: 兼容非 Windows 环境没有 msvcrt 的情况；若没有这行代码，非 Windows 测试会在导入阶段失败。
    msvcrt = None  # type: ignore[assignment]  # 修改代码+RuntimeFileSafetyFallback: 用 None 表示当前平台没有 Windows 字节锁；若没有这行代码，后续平台判断没有明确状态。


ATOMIC_REPLACE_RETRY_DELAYS_SECONDS = (0.05, 0.1, 0.2, 0.4, 0.8)  # 修改代码+RuntimeFileSafetyFallback: 定义 Windows 文件替换被短暂占用时的退避节奏；若没有这行代码，可见终端并发读写 state.json 时会直接失败。
WINDOWS_BYTE_LOCK_LENGTH = 64  # 新增代码+RuntimeFileSafetyFallback: 给 Windows msvcrt 锁保留一个小字节区域；若没有这行代码，锁区域大小会散落在代码里难以维护。
LOCK_RETRY_SLEEP_SECONDS = 0.02  # 修改代码+RuntimeFileSafetyFallback: 定义等待锁释放时的短暂停顿；若没有这行代码，等待锁会忙等占用 CPU。


def _replace_file_with_retries(temp_path: Path, target: Path) -> None:  # 修改代码+RuntimeFileSafetyFallback: 用可重试方式完成临时文件到目标文件的原子替换；若没有这段函数，PermissionError 不会自愈。
    last_error: PermissionError | None = None  # 修改代码+RuntimeFileSafetyFallback: 保存最后一次拒绝访问错误；若没有这行代码，重试耗尽后无法返回真实异常原因。
    retry_delays = (0.0, *ATOMIC_REPLACE_RETRY_DELAYS_SECONDS)  # 修改代码+RuntimeFileSafetyFallback: 第一次立即尝试，失败后再按退避等待；若没有这行代码，正常写入会被无故延迟。
    for retry_delay in retry_delays:  # 修改代码+RuntimeFileSafetyFallback: 逐次尝试替换文件；若没有这行代码，短暂锁冲突没有恢复机会。
        if retry_delay > 0:  # 修改代码+RuntimeFileSafetyFallback: 只有重试阶段才需要等待；若没有这行代码，第一次正常写入也会慢一拍。
            time.sleep(retry_delay)  # 修改代码+RuntimeFileSafetyFallback: 给 Windows、杀毒软件或另一个读进程释放句柄的时间；若没有这行代码，重试会变成忙等。
        try:  # 修改代码+RuntimeFileSafetyFallback: 捕获可恢复的替换失败；若没有这行代码，第一次拒绝访问会直接中断真实终端验收。
            os.replace(str(temp_path), str(target))  # 修改代码+RuntimeFileSafetyFallback: 首选仍使用原子 replace 写入最终文件；若没有这行代码，崩溃时可能留下半个 JSON。
            return  # 修改代码+RuntimeFileSafetyFallback: 替换成功后立即结束；若没有这行代码，后续重试会重复操作已不存在的临时文件。
        except PermissionError as error:  # 修改代码+RuntimeFileSafetyFallback: 只把拒绝访问视为可重试锁冲突；若没有这行代码，真实 Windows 共享冲突无法恢复。
            last_error = error  # 修改代码+RuntimeFileSafetyFallback: 记录最近一次失败；若没有这行代码，重试耗尽后会丢失原始错误。
    if last_error is not None:  # 修改代码+RuntimeFileSafetyFallback: 重试耗尽且确实有错误时进入失败返回；若没有这行代码，类型检查和异常语义不清楚。
        raise last_error  # 修改代码+RuntimeFileSafetyFallback: 抛回最后一次真实拒绝访问错误；若没有这行代码，调用方无法知道写入失败原因。


def _best_effort_unlink(path: Path) -> None:  # 新增代码+RuntimeFileSafetyFallback: 封装“能删就删、删不了不遮蔽主流程”的清理策略；若没有这段函数，当前工作区拒绝删除会再次拖垮 CLI。
    try:  # 新增代码+RuntimeFileSafetyFallback: 清理文件本身也可能失败，所以必须包住；若没有这行代码，清理失败会盖过真正业务结果。
        path.unlink(missing_ok=True)  # 新增代码+RuntimeFileSafetyFallback: 尝试删除临时文件或可选锁文件；若没有这行代码，允许删除的环境会堆积垃圾文件。
    except OSError:  # 新增代码+RuntimeFileSafetyFallback: 当前 Windows 工作区可能拒绝 unlink；若没有这行代码，WinError 5 会让已经成功的写入被判失败。
        pass  # 新增代码+RuntimeFileSafetyFallback: 删除失败时保留主流程结果；若没有这行代码，except 语法不完整。


class FileLock:  # 修改代码+RuntimeFileSafetyFallback: 用跨进程锁保护 JSON 状态读写；若没有这个类，多 worker 可能同时修改同一个文件。
    def __init__(self, lock_path: str | Path, timeout_seconds: float = 5.0) -> None:  # 修改代码+RuntimeFileSafetyFallback: 初始化锁路径和等待时间；若没有这行代码，调用方无法指定锁文件。
        self.lock_path = Path(lock_path)  # 修改代码+RuntimeFileSafetyFallback: 规范化锁路径；若没有这行代码，后续路径操作不稳定。
        self.timeout_seconds = max(0.1, float(timeout_seconds))  # 修改代码+RuntimeFileSafetyFallback: 限制最小等待时间；若没有这行代码，0 秒锁会让正常竞争过早失败。
        self._fd: int | None = None  # 修改代码+RuntimeFileSafetyFallback: 保存当前进程持有的文件描述符；若没有这行代码，释放锁时不知道关哪个句柄。
        self._windows_byte_lock_acquired = False  # 新增代码+RuntimeFileSafetyFallback: 记录是否已拿到 Windows 字节锁；若没有这行代码，退出时可能错误解锁未持有区域。

    def __enter__(self) -> "FileLock":  # 修改代码+RuntimeFileSafetyFallback: 支持 with FileLock(...) 语法；若没有这行代码，调用方容易忘记释放锁。
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)  # 修改代码+RuntimeFileSafetyFallback: 确保锁目录存在；若没有这行代码，首次加锁会因目录缺失失败。
        if os.name == "nt" and msvcrt is not None:  # 新增代码+RuntimeFileSafetyFallback: Windows 下优先使用句柄级字节锁；若没有这行代码，锁文件删不掉会永久阻塞后续运行。
            return self._enter_windows_byte_lock()  # 新增代码+RuntimeFileSafetyFallback: 进入不依赖删除文件的 Windows 锁路径；若没有这行代码，真实终端验收仍会被 mutex unlink 拒绝卡住。
        return self._enter_exclusive_file_lock()  # 修改代码+RuntimeFileSafetyFallback: 非 Windows 环境继续使用独占创建文件锁；若没有这行代码，跨平台锁能力会丢失。

    def _enter_windows_byte_lock(self) -> "FileLock":  # 新增代码+RuntimeFileSafetyFallback: 用 msvcrt 锁住锁文件的固定字节区域；若没有这段函数，Windows 无法摆脱 create/unlink 锁模型。
        deadline = time.time() + self.timeout_seconds  # 新增代码+RuntimeFileSafetyFallback: 计算等待截止时间；若没有这行代码，锁竞争没有边界。
        while True:  # 新增代码+RuntimeFileSafetyFallback: 循环尝试获取字节锁；若没有这行代码，短暂竞争会直接失败。
            flags = os.O_CREAT | os.O_RDWR  # 新增代码+RuntimeFileSafetyFallback: 以可读写方式打开锁文件；若没有这行代码，msvcrt 无法在句柄上加锁。
            if hasattr(os, "O_BINARY"):  # 新增代码+RuntimeFileSafetyFallback: Windows 文本模式可能影响底层字节位置；若没有这行代码，跨 Python/Windows 版本行为更不稳定。
                flags |= os.O_BINARY  # 新增代码+RuntimeFileSafetyFallback: 使用二进制方式打开锁文件；若没有这行代码，字节锁区域可能受文本转换影响。
            self._fd = os.open(str(self.lock_path), flags)  # 新增代码+RuntimeFileSafetyFallback: 打开或创建锁载体文件；若没有这行代码，后续没有可锁住的系统句柄。
            try:  # 新增代码+RuntimeFileSafetyFallback: 尝试获取非阻塞字节锁；若没有这行代码，锁竞争异常无法转为可控等待。
                os.lseek(self._fd, 0, os.SEEK_SET)  # 新增代码+RuntimeFileSafetyFallback: 把锁起点固定到文件开头；若没有这行代码，不同进程可能锁住不同区域。
                msvcrt.locking(self._fd, msvcrt.LK_NBLCK, WINDOWS_BYTE_LOCK_LENGTH)  # type: ignore[union-attr]  # 新增代码+RuntimeFileSafetyFallback: 非阻塞锁住固定字节区域；若没有这行代码，多进程仍可能同时写 JSON。
                self._windows_byte_lock_acquired = True  # 新增代码+RuntimeFileSafetyFallback: 标记锁已持有；若没有这行代码，退出阶段不知道是否需要解锁。
                os.ftruncate(self._fd, 0)  # 新增代码+RuntimeFileSafetyFallback: 清空旧 pid 信息；若没有这行代码，残留内容会误导排查。
                os.write(self._fd, str(os.getpid()).encode("utf-8", errors="replace"))  # 新增代码+RuntimeFileSafetyFallback: 写入当前进程号辅助排查；若没有这行代码，锁文件来源不清楚。
                return self  # 新增代码+RuntimeFileSafetyFallback: 成功持锁后返回自身；若没有这行代码，with 语句拿不到锁对象。
            except OSError as error:  # 新增代码+RuntimeFileSafetyFallback: 捕获锁已被占用或句柄锁失败；若没有这行代码，正常竞争会变成未处理异常。
                self._close_fd_best_effort()  # 新增代码+RuntimeFileSafetyFallback: 失败后关闭本次打开的句柄；若没有这行代码，重试会泄漏文件句柄。
                if time.time() >= deadline:  # 新增代码+RuntimeFileSafetyFallback: 判断是否超过等待时间；若没有这行代码，被占用的锁会让进程无限等待。
                    raise TimeoutError(f"等待文件锁超时：{self.lock_path}") from error  # 新增代码+RuntimeFileSafetyFallback: 超时给出明确锁路径；若没有这行代码，用户不知道卡在哪个文件。
                time.sleep(LOCK_RETRY_SLEEP_SECONDS)  # 新增代码+RuntimeFileSafetyFallback: 短暂休眠后重试；若没有这行代码，循环会忙等消耗 CPU。

    def _enter_exclusive_file_lock(self) -> "FileLock":  # 修改代码+RuntimeFileSafetyFallback: 为非 Windows 平台保留独占创建文件锁；若没有这段函数，非 Windows 状态写入没有互斥保护。
        deadline = time.time() + self.timeout_seconds  # 修改代码+RuntimeFileSafetyFallback: 计算等待截止时间；若没有这行代码，锁等待没有边界。
        while True:  # 修改代码+RuntimeFileSafetyFallback: 循环尝试创建独占锁文件；若没有这行代码，短暂竞争会直接失败。
            try:  # 修改代码+RuntimeFileSafetyFallback: 捕获锁已存在的竞争情况；若没有这行代码，正常并发会变成异常。
                self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)  # 修改代码+RuntimeFileSafetyFallback: 原子创建锁文件；若没有这行代码，多进程无法互斥。
                os.write(self._fd, str(os.getpid()).encode("utf-8", errors="replace"))  # 修改代码+RuntimeFileSafetyFallback: 写入进程号帮助排查卡锁；若没有这行代码，锁文件来源不清楚。
                return self  # 修改代码+RuntimeFileSafetyFallback: 成功持锁后返回自身；若没有这行代码，with 语句拿不到锁对象。
            except FileExistsError:  # 修改代码+RuntimeFileSafetyFallback: 锁文件已存在时进入等待；若没有这行代码，竞争会冒泡中断。
                if time.time() >= deadline:  # 修改代码+RuntimeFileSafetyFallback: 判断是否超过等待时间；若没有这行代码，坏锁会让进程无限等待。
                    raise TimeoutError(f"等待文件锁超时：{self.lock_path}")  # 修改代码+RuntimeFileSafetyFallback: 超时给出明确锁路径；若没有这行代码，用户不知道卡在哪个文件。
                time.sleep(LOCK_RETRY_SLEEP_SECONDS)  # 修改代码+RuntimeFileSafetyFallback: 短暂休眠后重试；若没有这行代码，循环会忙等消耗 CPU。

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:  # 修改代码+RuntimeFileSafetyFallback: 离开 with 时释放锁；若没有这行代码，异常路径会残留锁。
        if os.name == "nt" and msvcrt is not None:  # 新增代码+RuntimeFileSafetyFallback: Windows 字节锁需要先解锁再关闭句柄；若没有这行代码，锁可能等到进程退出才释放。
            self._release_windows_byte_lock()  # 新增代码+RuntimeFileSafetyFallback: 释放 Windows 字节锁并关闭句柄；若没有这行代码，后续写入可能被当前进程自己阻塞。
            _best_effort_unlink(self.lock_path)  # 新增代码+RuntimeFileSafetyFallback: 可删除时顺手清理锁载体文件；若没有这行代码，可删除环境会留下不必要的 mutex 文件。
            return None  # 新增代码+RuntimeFileSafetyFallback: Windows 锁释放完成后结束；若没有这行代码，会错误进入 create/unlink 释放路径。
        self._close_fd_best_effort()  # 修改代码+RuntimeFileSafetyFallback: 非 Windows 先关闭锁文件句柄；若没有这行代码，某些系统可能无法删除锁文件。
        _best_effort_unlink(self.lock_path)  # 修改代码+RuntimeFileSafetyFallback: 删除锁文件释放互斥且容忍删除失败；若没有这行代码，释放阶段错误会遮蔽业务异常。
        return None  # 修改代码+RuntimeFileSafetyFallback: 明确不吞掉 with 块中的业务异常；若没有这行代码，读者不清楚退出语义。

    def _release_windows_byte_lock(self) -> None:  # 新增代码+RuntimeFileSafetyFallback: 封装 Windows 字节锁释放流程；若没有这段函数，解锁和关闭句柄逻辑会散落在 __exit__。
        if self._fd is None:  # 新增代码+RuntimeFileSafetyFallback: 没有句柄时无需释放；若没有这行代码，未成功加锁也会尝试解锁空句柄。
            return  # 新增代码+RuntimeFileSafetyFallback: 直接结束空释放；若没有这行代码，后续 os.lseek 会收到 None。
        try:  # 新增代码+RuntimeFileSafetyFallback: 解锁本身也可能因为句柄状态失败；若没有这行代码，释放错误会遮蔽业务异常。
            if self._windows_byte_lock_acquired:  # 新增代码+RuntimeFileSafetyFallback: 只在确实拿到锁时解锁；若没有这行代码，未持锁路径会抛出错误。
                os.lseek(self._fd, 0, os.SEEK_SET)  # 新增代码+RuntimeFileSafetyFallback: 把解锁起点对齐到锁起点；若没有这行代码，可能解锁不到之前的区域。
                msvcrt.locking(self._fd, msvcrt.LK_UNLCK, WINDOWS_BYTE_LOCK_LENGTH)  # type: ignore[union-attr]  # 新增代码+RuntimeFileSafetyFallback: 释放固定字节区域；若没有这行代码，其他进程无法继续写入。
        finally:  # 新增代码+RuntimeFileSafetyFallback: 无论解锁是否成功都要尝试关闭句柄；若没有这行代码，异常路径会泄漏 fd。
            self._windows_byte_lock_acquired = False  # 新增代码+RuntimeFileSafetyFallback: 清除持锁标记；若没有这行代码，重复退出可能重复解锁。
            self._close_fd_best_effort()  # 新增代码+RuntimeFileSafetyFallback: 关闭底层 fd；若没有这行代码，Windows 会继续持有文件句柄。

    def _close_fd_best_effort(self) -> None:  # 修改代码+RuntimeFileSafetyFallback: 封装关闭 fd 的容错逻辑；若没有这段函数，多处关闭句柄容易重复出错。
        if self._fd is None:  # 修改代码+RuntimeFileSafetyFallback: 只有存在 fd 时才需要关闭；若没有这行代码，未加锁失败也会关闭空句柄。
            return  # 修改代码+RuntimeFileSafetyFallback: 空 fd 直接返回；若没有这行代码，后续 os.close 会收到 None。
        try:  # 修改代码+RuntimeFileSafetyFallback: 关闭句柄可能因外部状态失败；若没有这行代码，清理阶段错误会遮蔽主错误。
            os.close(self._fd)  # 修改代码+RuntimeFileSafetyFallback: 关闭锁文件描述符；若没有这行代码，Windows 可能持续持有锁文件。
        except OSError:  # 修改代码+RuntimeFileSafetyFallback: 容忍句柄已关闭等清理错误；若没有这行代码，重复释放会抛出无关异常。
            pass  # 修改代码+RuntimeFileSafetyFallback: 保留主流程结果；若没有这行代码，except 语法不完整。
        finally:  # 修改代码+RuntimeFileSafetyFallback: 无论关闭是否成功都清空本对象引用；若没有这行代码，后续可能重复关闭同一 fd。
            self._fd = None  # 修改代码+RuntimeFileSafetyFallback: 清空 fd 防止重复关闭；若没有这行代码，二次释放可能报错。


def atomic_write_text(path: str | Path, text: str) -> Path:  # 修改代码+RuntimeFileSafetyFallback: 用临时文件加 replace 原子写入文本，并在受限工作区可降级；若没有这段函数，半写 JSON 会损坏状态。
    target = Path(path)  # 修改代码+RuntimeFileSafetyFallback: 规范化目标路径；若没有这行代码，字符串路径后续操作不稳定。
    target.parent.mkdir(parents=True, exist_ok=True)  # 修改代码+RuntimeFileSafetyFallback: 确保父目录存在；若没有这行代码，首次写入会失败。
    temp_path = target.with_name(f".{target.name}.{secrets.token_hex(6)}.tmp")  # 修改代码+RuntimeFileSafetyFallback: 生成同目录临时文件；若没有这行代码，replace 可能跨盘不原子。
    temp_path.write_text(text, encoding="utf-8")  # 修改代码+RuntimeFileSafetyFallback: 先完整写入临时文件；若没有这行代码，目标文件会被直接半写。
    try:  # 修改代码+RuntimeFileSafetyFallback: 包住替换过程以便失败时清理或降级；若没有这行代码，重试耗尽会留下大堆 .tmp 文件。
        _replace_file_with_retries(temp_path, target)  # 修改代码+RuntimeFileSafetyFallback: 首选带退避的原子替换；若没有这行代码，Windows 短暂拒绝访问会拖垮真实验收。
    except PermissionError:  # 新增代码+RuntimeFileSafetyFallback: 当前工作区可能永久拒绝 os.replace；若没有这行代码，Phase95 CLI 会在报告落盘处失败。
        try:  # 新增代码+RuntimeFileSafetyFallback: 尝试用直接写入作为最后兜底；若没有这行代码，受限工作区无法保存状态。
            target.write_text(text, encoding="utf-8")  # 新增代码+RuntimeFileSafetyFallback: 直接写入目标文件保证可继续运行；若没有这行代码，replace 被拒绝时没有任何落盘结果。
        except BaseException:  # 新增代码+RuntimeFileSafetyFallback: 直接写入也失败时仍要清理临时文件；若没有这行代码，二次失败会留下更多垃圾文件。
            _best_effort_unlink(temp_path)  # 新增代码+RuntimeFileSafetyFallback: 尽力删除未使用的临时文件；若没有这行代码，可删除环境会残留 .tmp。
            raise  # 新增代码+RuntimeFileSafetyFallback: 把真正的直接写入错误交还调用方；若没有这行代码，调用方会误以为状态已保存。
        _best_effort_unlink(temp_path)  # 新增代码+RuntimeFileSafetyFallback: 降级成功后尽力清理临时文件；若没有这行代码，可删除环境会堆积无用 .tmp。
    except BaseException:  # 修改代码+RuntimeFileSafetyFallback: 捕获所有其他失败以尽量清理临时文件再继续抛出；若没有这行代码，KeyboardInterrupt 或 OSError 都可能留下脏临时文件。
        _best_effort_unlink(temp_path)  # 修改代码+RuntimeFileSafetyFallback: 删除未能替换的临时文件；若没有这行代码，status 目录会不断堆积无用 .tmp。
        raise  # 修改代码+RuntimeFileSafetyFallback: 把原始写入错误交还调用方；若没有这行代码，调用方会误以为状态已成功保存。
    return target  # 修改代码+RuntimeFileSafetyFallback: 返回目标路径作为证据；若没有这行代码，调用方无法记录写入位置。


def atomic_write_json(path: str | Path, payload: Any) -> Path:  # 修改代码+RuntimeFileSafetyFallback: 原子或受控降级写入 JSON 对象；若没有这段函数，每个模块都要重复 dumps 和 replace。
    return atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")  # 修改代码+RuntimeFileSafetyFallback: 写入可读 UTF-8 JSON；若没有这行代码，状态文件不易审计。


def read_json_or_default(path: str | Path, default: Any, quarantine_dir: str | Path | None = None) -> Any:  # 修改代码+RuntimeFileSafetyFallback: 读取 JSON 并对损坏文件容错；若没有这段函数，半写状态会拖垮恢复。
    source = Path(path)  # 修改代码+RuntimeFileSafetyFallback: 规范化源路径；若没有这行代码，路径类型不统一。
    if not source.exists():  # 修改代码+RuntimeFileSafetyFallback: 文件不存在时返回默认值；若没有这行代码，首次运行会报错。
        return default  # 修改代码+RuntimeFileSafetyFallback: 返回调用方提供的默认对象；若没有这行代码，空状态无法启动。
    try:  # 修改代码+RuntimeFileSafetyFallback: 捕获 JSON 损坏或读取错误；若没有这行代码，坏文件会中断所有恢复。
        return json.loads(source.read_text(encoding="utf-8"))  # 修改代码+RuntimeFileSafetyFallback: 读取并解析 JSON；若没有这行代码，调用方拿不到结构化状态。
    except (OSError, json.JSONDecodeError):  # 修改代码+RuntimeFileSafetyFallback: 处理磁盘读取和 JSON 解析失败；若没有这行代码，半写文件无法跳过。
        if quarantine_dir is not None:  # 修改代码+RuntimeFileSafetyFallback: 如果调用方提供隔离目录；若没有这行代码，损坏证据无法保留。
            quarantine = Path(quarantine_dir)  # 修改代码+RuntimeFileSafetyFallback: 规范化隔离目录；若没有这行代码，移动目标路径不稳定。
            quarantine.mkdir(parents=True, exist_ok=True)  # 修改代码+RuntimeFileSafetyFallback: 确保隔离目录存在；若没有这行代码，移动坏文件会失败。
            target = quarantine / f"{source.name}.{int(time.time())}.bad"  # 修改代码+RuntimeFileSafetyFallback: 生成带时间戳的坏文件名；若没有这行代码，多次隔离可能覆盖。
            try:  # 修改代码+RuntimeFileSafetyFallback: 移动坏文件也需要容错；若没有这行代码，隔离失败会掩盖恢复默认值。
                source.replace(target)  # 修改代码+RuntimeFileSafetyFallback: 把坏文件移入 quarantine；若没有这行代码，后续仍会反复读坏文件。
            except OSError:  # 修改代码+RuntimeFileSafetyFallback: 忽略隔离失败；若没有这行代码，恢复流程会被二次错误阻断。
                pass  # 修改代码+RuntimeFileSafetyFallback: 保持返回默认值；若没有这行代码，except 语法不完整。
        return default  # 修改代码+RuntimeFileSafetyFallback: 损坏文件时返回默认值继续运行；若没有这行代码，系统无法自愈。


def append_jsonl(path: str | Path, row: dict[str, Any]) -> Path:  # 修改代码+RuntimeFileSafetyFallback: 追加一行 JSONL 事件；若没有这段函数，各模块事件写入格式会不一致。
    target = Path(path)  # 修改代码+RuntimeFileSafetyFallback: 规范化事件路径；若没有这行代码，字符串路径后续操作不稳定。
    target.parent.mkdir(parents=True, exist_ok=True)  # 修改代码+RuntimeFileSafetyFallback: 确保事件目录存在；若没有这行代码，首次事件写入会失败。
    line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"  # 修改代码+RuntimeFileSafetyFallback: 构造完整单行 JSON；若没有这行代码，事件日志难以按行回放。
    with target.open("a", encoding="utf-8", newline="") as file_handle:  # 修改代码+RuntimeFileSafetyFallback: 追加模式打开文件；若没有这行代码，新事件会覆盖旧事件。
        file_handle.write(line)  # 修改代码+RuntimeFileSafetyFallback: 写入单行事件；若没有这行代码，事件不会落盘。
    return target  # 修改代码+RuntimeFileSafetyFallback: 返回事件文件路径；若没有这行代码，调用方无法记录证据位置。


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:  # 修改代码+RuntimeFileSafetyFallback: 读取 JSONL 并跳过坏行；若没有这段函数，单行损坏会拖垮状态页。
    source = Path(path)  # 修改代码+RuntimeFileSafetyFallback: 规范化事件路径；若没有这行代码，路径类型不统一。
    if not source.exists():  # 修改代码+RuntimeFileSafetyFallback: 没有事件文件时返回空列表；若没有这行代码，新状态页会报错。
        return []  # 修改代码+RuntimeFileSafetyFallback: 返回空事件列表；若没有这行代码，调用方要重复兜底。
    rows: list[dict[str, Any]] = []  # 修改代码+RuntimeFileSafetyFallback: 准备累计事件对象；若没有这行代码，函数没有返回容器。
    for raw_line in source.read_text(encoding="utf-8").splitlines():  # 修改代码+RuntimeFileSafetyFallback: 按行读取 JSONL；若没有这行代码，多事件无法解析。
        if not raw_line.strip():  # 修改代码+RuntimeFileSafetyFallback: 跳过空行；若没有这行代码，手工编辑空行会导致 JSON 错误。
            continue  # 修改代码+RuntimeFileSafetyFallback: 继续下一行；若没有这行代码，空行无法容错。
        try:  # 修改代码+RuntimeFileSafetyFallback: 单行解析失败时容错；若没有这行代码，半写事件会拖垮所有事件。
            parsed = json.loads(raw_line)  # 修改代码+RuntimeFileSafetyFallback: 解析当前 JSON 行；若没有这行代码，事件只能是字符串。
        except json.JSONDecodeError:  # 修改代码+RuntimeFileSafetyFallback: 处理坏行；若没有这行代码，损坏行会抛出异常。
            continue  # 修改代码+RuntimeFileSafetyFallback: 跳过坏行保留其他事件；若没有这行代码，审计能力会被单行破坏。
        if isinstance(parsed, dict):  # 修改代码+RuntimeFileSafetyFallback: 只接受对象事件；若没有这行代码，数组或字符串会污染事件列表。
            rows.append(parsed)  # 修改代码+RuntimeFileSafetyFallback: 保存解析成功的事件；若没有这行代码，调用方拿不到事件。
    return rows  # 修改代码+RuntimeFileSafetyFallback: 返回事件对象列表；若没有这行代码，状态渲染无数据。
