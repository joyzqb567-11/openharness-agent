"""OpenHarness Desktop OpenAI 模型注册表。"""  # 新增代码+OpenAIModelRegistry：说明本模块只保存安全模型状态；如果没有这行，维护者容易把 token/account 私密信息放进模型缓存。

from __future__ import annotations  # 新增代码+OpenAIModelRegistry：启用延迟类型解析；如果没有这行，类型注解在旧解释顺序下更脆弱。

import json  # 新增代码+OpenAIModelRegistry：读写模型注册表 JSON；如果没有这行，last-known-good 无法持久化。
import time  # 新增代码+OpenAIModelRegistry：记录模型探针更新时间；如果没有这行，状态新旧不可判断。
from pathlib import Path  # 新增代码+OpenAIModelRegistry：处理 workspace 和 memory 路径；如果没有这行，Windows 路径容易出错。
from typing import Any  # 新增代码+OpenAIModelRegistry：标注 JSON-like 设置对象；如果没有这行，输入边界不清楚。


OPENAI_MODEL_REGISTRY_SCHEMA_VERSION = 1  # 新增代码+OpenAIModelRegistry：声明模型注册表 schema；如果没有这行，未来迁移无法判断文件版本。
STATIC_OPENAI_MODEL_IDS = ("gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.3-codex-spark")  # 新增代码+OpenAIModelRegistry：定义 OpenAI 本地静态候选模型；如果没有这行，模型菜单没有基础列表。
OPENAI_MODEL_STATES = {"unknown", "available", "not_supported_for_account", "auth_failed", "rate_limited", "probe_failed"}  # 新增代码+OpenAIModelRegistry：定义允许的探针状态；如果没有这行，任意字符串会进入 UI。


def openai_model_registry_file(workspace: str | Path) -> Path:  # 新增代码+OpenAIModelRegistry：函数段开始，定位 OpenAI 模型注册表文件；如果没有这段，多模块会各自硬编码路径。
    return Path(workspace).expanduser().resolve() / "memory" / "gui_provider_settings" / "openai_model_registry.json"  # 新增代码+OpenAIModelRegistry：返回安全模型缓存路径；如果没有这行，缓存可能写到真实 token 文件旁的错误位置。
# 新增代码+OpenAIModelRegistry：函数段结束，openai_model_registry_file 到此结束；如果没有边界说明，初学者不易看出它只负责路径。


def _empty_registry() -> dict[str, Any]:  # 新增代码+OpenAIModelRegistry：函数段开始，生成空模型注册表；如果没有这段，首次加载要到处判空。
    return {"schema_version": OPENAI_MODEL_REGISTRY_SCHEMA_VERSION, "probe_results": {}, "last_known_good_models": [], "updated_at": 0.0}  # 新增代码+OpenAIModelRegistry：返回不含 token/account 的空结构；如果没有这行，调用方拿不到稳定字段。
# 新增代码+OpenAIModelRegistry：函数段结束，_empty_registry 到此结束；如果没有边界说明，初学者不易看出它只返回骨架。


def load_openai_model_registry(workspace: str | Path) -> dict[str, Any]:  # 新增代码+OpenAIModelRegistry：函数段开始，读取模型注册表；如果没有这段，探针结果和 last-known-good 无法恢复。
    path = openai_model_registry_file(workspace)  # 新增代码+OpenAIModelRegistry：定位注册表文件；如果没有这行，读取不知道目标路径。
    if not path.exists():  # 新增代码+OpenAIModelRegistry：处理首次使用无文件；如果没有这行，第一次打开模型菜单会报错。
        return _empty_registry()  # 新增代码+OpenAIModelRegistry：返回空注册表；如果没有这行，调用方要自己处理 FileNotFoundError。
    try:  # 新增代码+OpenAIModelRegistry：保护 JSON 解析；如果没有这行，坏缓存会让 provider settings 500。
        raw = json.loads(path.read_text(encoding="utf-8"))  # 新增代码+OpenAIModelRegistry：读取并解析注册表；如果没有这行，缓存不会生效。
    except json.JSONDecodeError:  # 新增代码+OpenAIModelRegistry：处理损坏 JSON；如果没有这行，坏文件无法自恢复。
        return _empty_registry()  # 新增代码+OpenAIModelRegistry：坏文件时返回空注册表；如果没有这行，GUI 无法打开。
    if not isinstance(raw, dict):  # 新增代码+OpenAIModelRegistry：防御非对象 JSON；如果没有这行，数组/字符串会污染状态。
        return _empty_registry()  # 新增代码+OpenAIModelRegistry：非对象视为空；如果没有这行，后续 get() 可能异常。
    probe_results = raw.get("probe_results", {}) if isinstance(raw.get("probe_results", {}), dict) else {}  # 新增代码+OpenAIModelRegistry：读取探针结果区块；如果没有这行，坏 probe_results 会拖垮菜单。
    last_known_good = raw.get("last_known_good_models", []) if isinstance(raw.get("last_known_good_models", []), list) else []  # 新增代码+OpenAIModelRegistry：读取 last-known-good 列表；如果没有这行，坏列表会污染模型。
    return {"schema_version": OPENAI_MODEL_REGISTRY_SCHEMA_VERSION, "probe_results": probe_results, "last_known_good_models": [str(model_id) for model_id in last_known_good if str(model_id).strip()], "updated_at": float(raw.get("updated_at", 0.0) or 0.0)}  # 新增代码+OpenAIModelRegistry：返回清洗后的安全注册表；如果没有这行，坏类型可能进入 UI。
# 新增代码+OpenAIModelRegistry：函数段结束，load_openai_model_registry 到此结束；如果没有边界说明，初学者不易看出它只读安全模型状态。


def save_openai_model_registry(workspace: str | Path, registry: dict[str, Any]) -> None:  # 新增代码+OpenAIModelRegistry：函数段开始，原子保存模型注册表；如果没有这段，探针结果无法持久化。
    path = openai_model_registry_file(workspace)  # 新增代码+OpenAIModelRegistry：定位注册表路径；如果没有这行，保存不知道写到哪里。
    path.parent.mkdir(parents=True, exist_ok=True)  # 新增代码+OpenAIModelRegistry：确保目录存在；如果没有这行，首次保存会失败。
    safe_registry = {"schema_version": OPENAI_MODEL_REGISTRY_SCHEMA_VERSION, "probe_results": registry.get("probe_results", {}) if isinstance(registry.get("probe_results", {}), dict) else {}, "last_known_good_models": registry.get("last_known_good_models", []) if isinstance(registry.get("last_known_good_models", []), list) else [], "updated_at": float(registry.get("updated_at", time.time()) or time.time())}  # 新增代码+OpenAIModelRegistry：只保存安全模型字段；如果没有这行，外部 token/account 字段可能混入缓存。
    temp_path = path.with_suffix(".tmp")  # 新增代码+OpenAIModelRegistry：准备临时文件路径；如果没有这行，无法先写完整再替换。
    temp_path.write_text(json.dumps(safe_registry, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")  # 新增代码+OpenAIModelRegistry：写入格式化安全 JSON；如果没有这行，模型状态不会落盘。
    temp_path.replace(path)  # 新增代码+OpenAIModelRegistry：原子替换目标文件；如果没有这行，崩溃时可能留下半写缓存。
# 新增代码+OpenAIModelRegistry：函数段结束，save_openai_model_registry 到此结束；如果没有边界说明，初学者不易看出它只保存模型字段。


def save_openai_model_probe_result(workspace: str | Path, model_id: str, state: str, message: str = "") -> dict[str, Any]:  # 新增代码+OpenAIModelRegistry：函数段开始，保存单个模型探针状态；如果没有这段，Direct SSE probe 结果无法进入模型菜单。
    clean_model_id = str(model_id or "").strip()  # 新增代码+OpenAIModelRegistry：清理模型 id；如果没有这行，空白模型可能污染缓存。
    clean_state = str(state or "unknown").strip()  # 新增代码+OpenAIModelRegistry：清理状态值；如果没有这行，None 会进入状态字段。
    if clean_state not in OPENAI_MODEL_STATES:  # 新增代码+OpenAIModelRegistry：限制状态枚举；如果没有这行，前端无法稳定渲染状态。
        clean_state = "probe_failed"  # 新增代码+OpenAIModelRegistry：未知状态收敛为 probe_failed；如果没有这行，坏状态会原样进入 UI。
    registry = load_openai_model_registry(workspace)  # 新增代码+OpenAIModelRegistry：读取现有注册表；如果没有这行，保存一个结果会覆盖其它结果。
    probe_results = registry.setdefault("probe_results", {})  # 新增代码+OpenAIModelRegistry：获取探针结果区块；如果没有这行，无法写入模型状态。
    probe_results[clean_model_id] = {"state": clean_state, "message": str(message or ""), "updated_at": time.time()}  # 新增代码+OpenAIModelRegistry：保存模型状态和低敏消息；如果没有这行，unsupported/rate_limited 等结果不会持久。
    registry["updated_at"] = time.time()  # 新增代码+OpenAIModelRegistry：更新注册表时间；如果没有这行，诊断看不出缓存新旧。
    save_openai_model_registry(workspace, registry)  # 新增代码+OpenAIModelRegistry：写回安全缓存；如果没有这行，探针结果只在内存存在。
    return registry  # 新增代码+OpenAIModelRegistry：返回更新后的注册表；如果没有这行，调用方无法立即读取结果。
# 新增代码+OpenAIModelRegistry：函数段结束，save_openai_model_probe_result 到此结束；如果没有边界说明，初学者不易看出它只保存状态。


def record_openai_last_known_good_model(workspace: str | Path, model_id: str) -> dict[str, Any]:  # 新增代码+OpenAIModelRegistry：函数段开始，记录完成过真实调用的模型；如果没有这段，探针失败后无法保留最后成功模型。
    clean_model_id = str(model_id or "").strip()  # 新增代码+OpenAIModelRegistry：清理模型 id；如果没有这行，空白模型可能进入 last-known-good。
    registry = load_openai_model_registry(workspace)  # 新增代码+OpenAIModelRegistry：读取现有注册表；如果没有这行，记录成功模型会覆盖探针结果。
    good_models = [str(item) for item in registry.get("last_known_good_models", []) if str(item).strip()]  # 新增代码+OpenAIModelRegistry：读取并清洗已有成功模型；如果没有这行，坏类型会污染缓存。
    if clean_model_id and clean_model_id not in good_models:  # 新增代码+OpenAIModelRegistry：只追加非空且未存在的模型；如果没有这行，列表会重复膨胀。
        good_models.append(clean_model_id)  # 新增代码+OpenAIModelRegistry：加入最后成功模型；如果没有这行，真实成功不会被缓存。
    registry["last_known_good_models"] = good_models  # 新增代码+OpenAIModelRegistry：写回成功模型列表；如果没有这行，save 看不到更新。
    registry["updated_at"] = time.time()  # 新增代码+OpenAIModelRegistry：更新注册表时间；如果没有这行，诊断看不出缓存新旧。
    save_openai_model_registry(workspace, registry)  # 新增代码+OpenAIModelRegistry：保存安全缓存；如果没有这行，last-known-good 重启后会丢。
    return registry  # 新增代码+OpenAIModelRegistry：返回更新后注册表；如果没有这行，调用方无法立即使用。
# 新增代码+OpenAIModelRegistry：函数段结束，record_openai_last_known_good_model 到此结束；如果没有边界说明，初学者不易看出它只记录模型 id。


def _model_visible(settings: dict[str, Any], model_id: str) -> bool:  # 新增代码+OpenAIModelRegistry：函数段开始，读取 OpenAI 模型可见性；如果没有这段，隐藏模型无法影响注册表输出。
    visibility = settings.get("model_visibility", {}) if isinstance(settings.get("model_visibility", {}), dict) else {}  # 新增代码+OpenAIModelRegistry：读取可见性区块；如果没有这行，坏配置会导致异常。
    return bool(visibility.get(f"openai:{model_id}", True))  # 新增代码+OpenAIModelRegistry：返回用户覆盖或默认可见；如果没有这行，模型菜单不尊重用户隐藏。
# 新增代码+OpenAIModelRegistry：函数段结束，_model_visible 到此结束；如果没有边界说明，初学者不易看出它只读可见性。


def build_openai_model_catalog_rows(workspace: str | Path, settings: dict[str, Any]) -> list[dict[str, Any]]:  # 新增代码+OpenAIModelRegistry：函数段开始，生成 provider catalog 可用的 OpenAI 模型行；如果没有这段，设置页仍会使用硬编码 gpt-4.1。
    registry = load_openai_model_registry(workspace)  # 新增代码+OpenAIModelRegistry：读取探针和 last-known-good 缓存；如果没有这行，模型行无法反映真实账号。
    probe_results = registry.get("probe_results", {}) if isinstance(registry.get("probe_results", {}), dict) else {}  # 新增代码+OpenAIModelRegistry：读取探针结果；如果没有这行，available/unsupported 状态无法进入 UI。
    ordered_model_ids: list[str] = list(STATIC_OPENAI_MODEL_IDS)  # 新增代码+OpenAIModelRegistry：从静态候选开始排序；如果没有这行，菜单没有基础模型。
    for model_id in probe_results.keys():  # 新增代码+OpenAIModelRegistry：追加探针发现但不在静态列表的模型；如果没有这行，账号可用新模型不会显示。
        if model_id not in ordered_model_ids:  # 新增代码+OpenAIModelRegistry：避免重复模型；如果没有这行，同一模型会出现两次。
            ordered_model_ids.append(str(model_id))  # 新增代码+OpenAIModelRegistry：加入探针模型；如果没有这行，probe_available_models 不会生效。
    for model_id in registry.get("last_known_good_models", []):  # 新增代码+OpenAIModelRegistry：追加最后成功模型；如果没有这行，探针失败时成功历史不会显示。
        if model_id not in ordered_model_ids:  # 新增代码+OpenAIModelRegistry：避免 last-known-good 重复已有模型；如果没有这行，菜单会重复。
            ordered_model_ids.append(str(model_id))  # 新增代码+OpenAIModelRegistry：加入最后成功模型；如果没有这行，last-known-good 不会显示。
    rows: list[dict[str, Any]] = []  # 新增代码+OpenAIModelRegistry：准备模型行列表；如果没有这行，后续无法累积输出。
    for model_id in ordered_model_ids:  # 新增代码+OpenAIModelRegistry：按三层来源顺序生成模型行；如果没有这行，catalog 没有模型。
        probe = probe_results.get(model_id, {}) if isinstance(probe_results.get(model_id, {}), dict) else {}  # 新增代码+OpenAIModelRegistry：读取单模型探针结果；如果没有这行，状态无法覆盖 unknown。
        state = str(probe.get("state", "unknown")) if probe else ("available" if model_id in registry.get("last_known_good_models", []) else "unknown")  # 新增代码+OpenAIModelRegistry：推导模型状态；如果没有这行，unsupported/available 无法显示。
        if state not in OPENAI_MODEL_STATES:  # 新增代码+OpenAIModelRegistry：防御坏状态；如果没有这行，前端可能收到未知 enum。
            state = "probe_failed"  # 新增代码+OpenAIModelRegistry：坏状态收敛为 probe_failed；如果没有这行，错误状态不可渲染。
        source = "probe_available_models" if probe else ("last_known_good_models" if model_id in registry.get("last_known_good_models", []) else "static_known_models")  # 新增代码+OpenAIModelRegistry：记录模型来源层；如果没有这行，诊断无法知道为何显示模型。
        rows.append({"id": model_id, "display_name": model_id.upper(), "provider_id": "openai", "visible": _model_visible(settings, model_id), "supports_tools": True, "supports_vision": True, "state": state, "source": source, "message": str(probe.get("message", "")) if probe else ""})  # 新增代码+OpenAIModelRegistry：生成安全模型行；如果没有这行，设置页没有模型状态和来源。
    return rows  # 新增代码+OpenAIModelRegistry：返回模型行；如果没有这行，调用方拿不到结果。
# 新增代码+OpenAIModelRegistry：函数段结束，build_openai_model_catalog_rows 到此结束；如果没有边界说明，初学者不易看出它只输出公开模型信息。


def build_openai_model_registry_payload(workspace: str | Path, settings: dict[str, Any] | None = None) -> dict[str, Any]:  # 新增代码+OpenAIModelRegistry：函数段开始，生成 bridge 可返回的模型注册表 payload；如果没有这段，前端无法单独刷新模型状态。
    safe_settings = settings if isinstance(settings, dict) else {}  # 新增代码+OpenAIModelRegistry：兼容无 settings 调用；如果没有这行，bridge endpoint 需要先读取 provider settings。
    registry = load_openai_model_registry(workspace)  # 新增代码+OpenAIModelRegistry：读取注册表；如果没有这行，payload 缺少更新时间和缓存。
    return {"ok": True, "schema_version": OPENAI_MODEL_REGISTRY_SCHEMA_VERSION, "provider_id": "openai", "models": build_openai_model_catalog_rows(workspace, safe_settings), "last_known_good_models": registry.get("last_known_good_models", []), "updated_at": registry.get("updated_at", 0.0)}  # 新增代码+OpenAIModelRegistry：返回不含 token/email 的模型状态；如果没有这行，bridge 无法响应前端。
# 新增代码+OpenAIModelRegistry：函数段结束，build_openai_model_registry_payload 到此结束；如果没有边界说明，初学者不易看出它是公开 payload。
