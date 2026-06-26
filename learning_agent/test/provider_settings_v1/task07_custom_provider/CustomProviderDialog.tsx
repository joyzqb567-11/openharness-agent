import { Plus, X } from "lucide-react"; // 新增代码+CustomProviderDialog：导入添加和关闭图标；如果没有这行，自定义 provider 表单按钮会缺少明确视觉意图。
import { useState, type FormEvent } from "react"; // 新增代码+CustomProviderDialog：导入 React 状态和表单事件类型；如果没有这行，弹窗无法管理本地输入状态。
import type { CustomProviderRequest } from "../../api/guiProviderTypes"; // 新增代码+CustomProviderDialog：导入保存自定义 provider 的请求类型；如果没有这行，前端 payload 形状会变成不透明对象。

export type CustomProviderModelRow = { id: string; displayName: string }; // 新增代码+CustomProviderDialog：定义模型输入行；如果没有这行，模型 id 和显示名会缺少统一类型。

export type CustomProviderHeaderRow = { key: string; value: string }; // 新增代码+CustomProviderDialog：定义 header 输入行；如果没有这行，自定义 header 配置会变成任意对象。

export type CustomProviderDialogState = { // 新增代码+CustomProviderDialog：类型段开始，描述整个自定义 provider 表单状态；如果没有这段，校验和 payload 构造无法共享同一形状。
  providerId: string; // 新增代码+CustomProviderDialog：保存 provider id 输入；如果没有这行，后端无法持久化自定义 provider。
  displayName: string; // 新增代码+CustomProviderDialog：保存显示名输入；如果没有这行，Provider 列表只能显示机器 id。
  baseUrl: string; // 新增代码+CustomProviderDialog：保存 OpenAI-compatible base URL；如果没有这行，探针和模型请求没有目标地址。
  apiKey: string; // 新增代码+CustomProviderDialog：保存本地 API key 输入；如果没有这行，用户无法连接自定义 provider。
  models: CustomProviderModelRow[]; // 新增代码+CustomProviderDialog：保存模型行数组；如果没有这行，Models 页不会知道自定义 provider 有哪些模型。
  headers: CustomProviderHeaderRow[]; // 新增代码+CustomProviderDialog：保存 header 行数组；如果没有这行，OpenAI-compatible gateway 场景无法配置额外 header。
}; // 新增代码+CustomProviderDialog：CustomProviderDialogState 类型结束；如果没有这行，TypeScript 类型语法不完整。

type CustomProviderDialogProps = { // 新增代码+CustomProviderDialog：类型段开始，定义弹窗对外输入；如果没有这段，父组件无法控制打开、关闭和保存。
  open: boolean; // 新增代码+CustomProviderDialog：保存弹窗是否打开；如果没有这行，关闭状态无法从 DOM 移除。
  pending: boolean; // 新增代码+CustomProviderDialog：保存保存等待态；如果没有这行，用户可能重复点击保存。
  errorMessage: string; // 新增代码+CustomProviderDialog：保存后端安全错误文案；如果没有这行，保存失败没有可见反馈。
  onClose: () => void; // 新增代码+CustomProviderDialog：保存关闭回调；如果没有这行，用户无法取消或关闭弹窗。
  onSave: (payload: CustomProviderRequest) => Promise<boolean> | boolean; // 新增代码+CustomProviderDialog：保存提交回调；如果没有这行，表单无法调用 GUI client。
}; // 新增代码+CustomProviderDialog：CustomProviderDialogProps 类型结束；如果没有这行，TypeScript 类型语法不完整。

const RESERVED_PROVIDER_IDS = new Set(["custom", "custom-provider-cta", "github-copilot", "openai", "google", "openrouter", "vercel"]); // 新增代码+CustomProviderDialog：定义系统保留 provider id；如果没有这行，自定义 provider 可能覆盖内置 provider 或虚拟 CTA。

const PROVIDER_ID_PATTERN = /^[a-z0-9][a-z0-9-]{1,62}$/; // 新增代码+CustomProviderDialog：定义 provider id 格式规则；如果没有这行，非法 id 会进入配置文件。

function initialCustomProviderState(): CustomProviderDialogState { // 新增代码+CustomProviderDialog：函数段开始，生成初始表单状态；如果没有这段，重置表单会重复手写对象。
  return { providerId: "", displayName: "", baseUrl: "", apiKey: "", models: [{ id: "", displayName: "" }], headers: [{ key: "", value: "" }] }; // 新增代码+CustomProviderDialog：返回空表单和一行模型/header；如果没有这行，弹窗打开时没有可输入的行。
} // 新增代码+CustomProviderDialog：函数段结束，initialCustomProviderState 到此结束；如果没有这行，函数语法不完整。

function trimmedModels(models: CustomProviderModelRow[]): CustomProviderModelRow[] { // 新增代码+CustomProviderDialog：函数段开始，清理模型行；如果没有这段，空格模型或空模型会进入保存 payload。
  return models.map((model) => ({ id: model.id.trim(), displayName: model.displayName.trim() })).filter((model) => model.id.length > 0 && model.displayName.length > 0); // 新增代码+CustomProviderDialog：只保留 id 和显示名都存在的模型；如果没有这行，后端会收到不完整模型。
} // 新增代码+CustomProviderDialog：函数段结束，trimmedModels 到此结束；如果没有这行，函数语法不完整。

function trimmedHeaders(headers: CustomProviderHeaderRow[]): CustomProviderHeaderRow[] { // 新增代码+CustomProviderDialog：函数段开始，清理 header 行；如果没有这段，空 header 行会被保存。
  return headers.map((header) => ({ key: header.key.trim(), value: header.value.trim() })).filter((header) => header.key.length > 0 && header.value.length > 0); // 新增代码+CustomProviderDialog：只保留 key/value 都存在的 header；如果没有这行，后端会收到无意义 header。
} // 新增代码+CustomProviderDialog：函数段结束，trimmedHeaders 到此结束；如果没有这行，函数语法不完整。

export function customProviderValidationError(state: CustomProviderDialogState): string { // 新增代码+CustomProviderDialog：函数段开始，返回蓝图要求的第一条校验错误；如果没有这段，表单会把坏输入直接交给后端。
  const providerId = state.providerId.trim(); // 新增代码+CustomProviderDialog：清理 provider id 空格；如果没有这行，前后空格会绕过格式判断。
  if (!PROVIDER_ID_PATTERN.test(providerId)) { // 新增代码+CustomProviderDialog：检查 id 是否只包含小写字母、数字和短横线；如果没有这行，非法 id 会进入配置文件。
    return "Provider ID 只能使用小写字母、数字和短横线"; // 新增代码+CustomProviderDialog：返回蓝图指定 id 格式文案；如果没有这行，用户不知道如何修正 id。
  } // 新增代码+CustomProviderDialog：id 格式分支结束；如果没有这行，条件块语法不完整。
  if (RESERVED_PROVIDER_IDS.has(providerId)) { // 新增代码+CustomProviderDialog：检查 id 是否为系统保留；如果没有这行，用户可能覆盖内置 provider。
    return "Provider ID 已被系统保留"; // 新增代码+CustomProviderDialog：返回蓝图指定保留 id 文案；如果没有这行，用户不知道要换 id。
  } // 新增代码+CustomProviderDialog：保留 id 分支结束；如果没有这行，条件块语法不完整。
  const baseUrl = state.baseUrl.trim(); // 新增代码+CustomProviderDialog：清理 base URL 空格；如果没有这行，前后空格会污染保存 payload。
  if (!baseUrl.startsWith("http://") && !baseUrl.startsWith("https://")) { // 新增代码+CustomProviderDialog：限制 base URL 协议；如果没有这行，非 HTTP endpoint 会进入探针流程。
    return "Base URL 必须以 http:// 或 https:// 开头"; // 新增代码+CustomProviderDialog：返回蓝图指定 URL 文案；如果没有这行，用户不知道 URL 格式要求。
  } // 新增代码+CustomProviderDialog：base URL 分支结束；如果没有这行，条件块语法不完整。
  if (trimmedModels(state.models).length === 0) { // 新增代码+CustomProviderDialog：检查至少一个完整模型；如果没有这行，Models 页会没有可显示模型。
    return "至少填写一个模型"; // 新增代码+CustomProviderDialog：返回蓝图指定模型缺失文案；如果没有这行，用户不知道必须填模型。
  } // 新增代码+CustomProviderDialog：模型校验分支结束；如果没有这行，条件块语法不完整。
  return ""; // 新增代码+CustomProviderDialog：没有错误时返回空字符串；如果没有这行，调用方无法区分通过和失败。
} // 新增代码+CustomProviderDialog：函数段结束，customProviderValidationError 到此结束；如果没有这行，函数语法不完整。

export function buildCustomProviderRequest(state: CustomProviderDialogState): CustomProviderRequest | null { // 新增代码+CustomProviderDialog：函数段开始，构造保存请求；如果没有这段，提交逻辑会散落在 JSX 里。
  if (customProviderValidationError(state).length > 0) { // 新增代码+CustomProviderDialog：先复用校验规则；如果没有这行，调用方可能构造出非法 payload。
    return null; // 新增代码+CustomProviderDialog：校验失败返回 null；如果没有这行，坏数据仍可能提交。
  } // 新增代码+CustomProviderDialog：校验失败分支结束；如果没有这行，条件块语法不完整。
  return { providerId: state.providerId.trim(), displayName: state.displayName.trim() || state.providerId.trim(), baseUrl: state.baseUrl.trim(), authMethodId: "api_key", fields: { api_key: state.apiKey.trim() }, headers: trimmedHeaders(state.headers), models: trimmedModels(state.models).map((model) => ({ ...model, visible: true })) }; // 新增代码+CustomProviderDialog：返回后端需要的保存 payload；如果没有这行，自定义 provider 无法落盘。
} // 新增代码+CustomProviderDialog：函数段结束，buildCustomProviderRequest 到此结束；如果没有这行，函数语法不完整。

export function CustomProviderDialog({ open, pending, errorMessage, onClose, onSave }: CustomProviderDialogProps): JSX.Element | null { // 新增代码+CustomProviderDialog：函数段开始，渲染自定义 provider 弹窗；如果没有这段，虚拟 CTA 点击后没有真实表单。
  const [formState, setFormState] = useState<CustomProviderDialogState>(() => initialCustomProviderState()); // 新增代码+CustomProviderDialog：保存表单本地状态；如果没有这行，输入框无法受控。
  const [localError, setLocalError] = useState(""); // 新增代码+CustomProviderDialog：保存前端校验错误；如果没有这行，用户看不到本地校验失败原因。
  const visibleError = localError || errorMessage; // 新增代码+CustomProviderDialog：优先显示本地错误再显示后端错误；如果没有这行，错误展示逻辑会散落。
  if (!open) { // 新增代码+CustomProviderDialog：处理关闭状态；如果没有这行，弹窗关闭后仍占用 DOM。
    return null; // 新增代码+CustomProviderDialog：关闭时不渲染；如果没有这行，隐藏状态仍可能保留可点击表单。
  } // 新增代码+CustomProviderDialog：关闭状态分支结束；如果没有这行，条件块语法不完整。
  function updateTextField(field: "providerId" | "displayName" | "baseUrl" | "apiKey", value: string): void { // 新增代码+CustomProviderDialog：函数段开始，更新普通文本字段；如果没有这段，每个 input 都要重复 setState。
    setFormState((current) => ({ ...current, [field]: value })); // 新增代码+CustomProviderDialog：只更新目标字段；如果没有这行，输入框不会改变状态。
  } // 新增代码+CustomProviderDialog：函数段结束，updateTextField 到此结束；如果没有这行，函数语法不完整。
  function updateModelRow(index: number, field: keyof CustomProviderModelRow, value: string): void { // 新增代码+CustomProviderDialog：函数段开始，更新模型行；如果没有这段，用户无法编辑模型列表。
    setFormState((current) => ({ ...current, models: current.models.map((model, modelIndex) => modelIndex === index ? { ...model, [field]: value } : model) })); // 新增代码+CustomProviderDialog：只更新被编辑的模型行；如果没有这行，模型输入不会保存到状态。
  } // 新增代码+CustomProviderDialog：函数段结束，updateModelRow 到此结束；如果没有这行，函数语法不完整。
  function addModelRow(): void { // 新增代码+CustomProviderDialog：函数段开始，添加模型行；如果没有这段，用户只能配置一个模型。
    setFormState((current) => ({ ...current, models: [...current.models, { id: "", displayName: "" }] })); // 新增代码+CustomProviderDialog：追加空模型行；如果没有这行，新增按钮没有效果。
  } // 新增代码+CustomProviderDialog：函数段结束，addModelRow 到此结束；如果没有这行，函数语法不完整。
  function updateHeaderRow(index: number, field: keyof CustomProviderHeaderRow, value: string): void { // 新增代码+CustomProviderDialog：函数段开始，更新 header 行；如果没有这段，用户无法编辑 gateway header。
    setFormState((current) => ({ ...current, headers: current.headers.map((header, headerIndex) => headerIndex === index ? { ...header, [field]: value } : header) })); // 新增代码+CustomProviderDialog：只更新被编辑的 header 行；如果没有这行，header 输入不会保存到状态。
  } // 新增代码+CustomProviderDialog：函数段结束，updateHeaderRow 到此结束；如果没有这行，函数语法不完整。
  function addHeaderRow(): void { // 新增代码+CustomProviderDialog：函数段开始，添加 header 行；如果没有这段，用户只能配置一个 header。
    setFormState((current) => ({ ...current, headers: [...current.headers, { key: "", value: "" }] })); // 新增代码+CustomProviderDialog：追加空 header 行；如果没有这行，新增 header 按钮没有效果。
  } // 新增代码+CustomProviderDialog：函数段结束，addHeaderRow 到此结束；如果没有这行，函数语法不完整。
  function resetAndClose(): void { // 新增代码+CustomProviderDialog：函数段开始，关闭并清理敏感输入；如果没有这段，取消后 API key 可能留在 renderer state。
    setFormState(initialCustomProviderState()); // 新增代码+CustomProviderDialog：重置表单状态；如果没有这行，API key 和 header value 会残留。
    setLocalError(""); // 新增代码+CustomProviderDialog：清空本地错误；如果没有这行，下次打开会看到旧错误。
    onClose(); // 新增代码+CustomProviderDialog：通知父组件关闭；如果没有这行，弹窗无法真正关闭。
  } // 新增代码+CustomProviderDialog：函数段结束，resetAndClose 到此结束；如果没有这行，函数语法不完整。
  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> { // 新增代码+CustomProviderDialog：函数段开始，处理保存提交；如果没有这段，保存按钮没有行为。
    event.preventDefault(); // 新增代码+CustomProviderDialog：阻止表单刷新 renderer；如果没有这行，Electron 窗口可能整页刷新。
    const validationError = customProviderValidationError(formState); // 新增代码+CustomProviderDialog：计算本地校验错误；如果没有这行，坏输入会打到后端。
    if (validationError.length > 0) { // 新增代码+CustomProviderDialog：处理校验失败；如果没有这行，错误不会显示。
      setLocalError(validationError); // 新增代码+CustomProviderDialog：显示蓝图指定错误文案；如果没有这行，用户不知道如何修复输入。
      return; // 新增代码+CustomProviderDialog：阻止继续保存；如果没有这行，校验失败仍会调用 onSave。
    } // 新增代码+CustomProviderDialog：校验失败分支结束；如果没有这行，条件块语法不完整。
    const payload = buildCustomProviderRequest(formState); // 新增代码+CustomProviderDialog：构造保存 payload；如果没有这行，onSave 没有输入。
    if (payload === null) { // 新增代码+CustomProviderDialog：防御性处理构造失败；如果没有这行，null payload 可能传给父组件。
      return; // 新增代码+CustomProviderDialog：构造失败时退出；如果没有这行，后续会访问 null。
    } // 新增代码+CustomProviderDialog：payload 防御分支结束；如果没有这行，条件块语法不完整。
    setLocalError(""); // 新增代码+CustomProviderDialog：提交前清空本地错误；如果没有这行，旧错误可能在保存中继续显示。
    const saved = await onSave(payload); // 新增代码+CustomProviderDialog：调用父组件保存；如果没有这行，自定义 provider 不会写入后端。
    if (saved) { // 新增代码+CustomProviderDialog：只在保存成功后清理和关闭；如果没有这行，失败时用户输入会被误清空。
      resetAndClose(); // 新增代码+CustomProviderDialog：成功后清空 API key/header 并关闭；如果没有这行，敏感值会继续留在表单状态。
    } // 新增代码+CustomProviderDialog：保存成功分支结束；如果没有这行，条件块语法不完整。
  } // 新增代码+CustomProviderDialog：函数段结束，handleSubmit 到此结束；如果没有这行，函数语法不完整。
  return ( // 新增代码+CustomProviderDialog：返回弹窗 JSX；如果没有这行，组件没有 UI 输出。
    <div className="provider-connect-overlay" role="presentation"> {/* 新增代码+CustomProviderDialog：复用连接弹窗遮罩；如果没有这层，自定义表单不会覆盖 Provider 列表。 */}
      <form className="custom-provider-dialog" onSubmit={(event) => { void handleSubmit(event); }} role="dialog" aria-modal="true" aria-label="自定义提供商"> {/* 新增代码+CustomProviderDialog：渲染自定义 provider 表单；如果没有这行，读屏器无法识别弹窗。 */}
        <header className="provider-connect-header"> {/* 新增代码+CustomProviderDialog：渲染标题行；如果没有这层，标题和关闭按钮无法对齐。 */}
          <strong>自定义提供商</strong> {/* 新增代码+CustomProviderDialog：显示弹窗标题；如果没有这行，用户不知道正在添加 provider。 */}
          <button aria-label="关闭自定义提供商弹窗" className="provider-connect-close" type="button" onClick={resetAndClose}><X aria-hidden={true} size={14} /></button> {/* 新增代码+CustomProviderDialog：渲染关闭按钮并清理敏感状态；如果没有这行，用户无法取消添加。 */}
        </header> {/* 新增代码+CustomProviderDialog：标题行结束；如果没有这行，JSX 结构不完整。 */}
        <div className="custom-provider-grid"> {/* 新增代码+CustomProviderDialog：渲染基础字段网格；如果没有这层，字段布局会散落。 */}
          <label className="provider-connect-field"><span>Provider ID</span><input value={formState.providerId} onChange={(event) => updateTextField("providerId", event.target.value)} /></label> {/* 新增代码+CustomProviderDialog：渲染 provider id 输入；如果没有这行，用户无法填写稳定 id。 */}
          <label className="provider-connect-field"><span>显示名称</span><input value={formState.displayName} onChange={(event) => updateTextField("displayName", event.target.value)} /></label> {/* 新增代码+CustomProviderDialog：渲染显示名输入；如果没有这行，列表无法显示可读名称。 */}
          <label className="provider-connect-field custom-provider-wide"><span>Base URL</span><input value={formState.baseUrl} onChange={(event) => updateTextField("baseUrl", event.target.value)} placeholder="https://api.example.com/v1" /></label> {/* 新增代码+CustomProviderDialog：渲染 base URL 输入；如果没有这行，provider 没有 OpenAI-compatible endpoint。 */}
          <label className="provider-connect-field custom-provider-wide"><span>API Key</span><input autoComplete="off" type="password" value={formState.apiKey} onChange={(event) => updateTextField("apiKey", event.target.value)} /></label> {/* 新增代码+CustomProviderDialog：渲染密码型 API key 输入；如果没有这行，密钥可能明文显示。 */}
        </div> {/* 新增代码+CustomProviderDialog：基础字段网格结束；如果没有这行，JSX 结构不完整。 */}
        <section className="custom-provider-section"> {/* 新增代码+CustomProviderDialog：渲染模型配置区域；如果没有这层，模型输入没有语义分组。 */}
          <div className="custom-provider-section-title"><strong>模型</strong><button className="settings-provider-secondary-button" type="button" onClick={addModelRow}><Plus aria-hidden={true} size={14} /><span>添加模型</span></button></div> {/* 新增代码+CustomProviderDialog：渲染模型标题和添加按钮；如果没有这行，用户无法添加多模型。 */}
          {formState.models.map((model, index) => ( // 新增代码+CustomProviderDialog：遍历模型输入行；如果没有这行，模型状态不会渲染。
            <div className="custom-provider-row" key={`model-${index}`}> {/* 新增代码+CustomProviderDialog：渲染单个模型行；如果没有这层，两个模型输入无法对齐。 */}
              <input aria-label="模型 ID" placeholder="模型 ID" value={model.id} onChange={(event) => updateModelRow(index, "id", event.target.value)} /> {/* 新增代码+CustomProviderDialog：渲染模型 id 输入；如果没有这行，后端无法保存模型 id。 */}
              <input aria-label="模型显示名称" placeholder="显示名称" value={model.displayName} onChange={(event) => updateModelRow(index, "displayName", event.target.value)} /> {/* 新增代码+CustomProviderDialog：渲染模型显示名输入；如果没有这行，模型页缺少可读名称。 */}
            </div> // 新增代码+CustomProviderDialog：模型行结束；如果没有这行，JSX 结构不完整。
          ))} {/* 新增代码+CustomProviderDialog：模型行遍历结束；如果没有这行，JSX 表达式不完整。 */}
        </section> {/* 新增代码+CustomProviderDialog：模型配置区域结束；如果没有这行，JSX 结构不完整。 */}
        <section className="custom-provider-section"> {/* 新增代码+CustomProviderDialog：渲染 headers 配置区域；如果没有这层，header 输入没有语义分组。 */}
          <div className="custom-provider-section-title"><strong>Headers</strong><button className="settings-provider-secondary-button" type="button" onClick={addHeaderRow}><Plus aria-hidden={true} size={14} /><span>添加 Header</span></button></div> {/* 新增代码+CustomProviderDialog：渲染 header 标题和添加按钮；如果没有这行，用户无法添加多个 header。 */}
          {formState.headers.map((header, index) => ( // 新增代码+CustomProviderDialog：遍历 header 输入行；如果没有这行，header 状态不会渲染。
            <div className="custom-provider-row" key={`header-${index}`}> {/* 新增代码+CustomProviderDialog：渲染单个 header 行；如果没有这层，key/value 输入无法对齐。 */}
              <input aria-label="Header Key" placeholder="Header Key" value={header.key} onChange={(event) => updateHeaderRow(index, "key", event.target.value)} /> {/* 新增代码+CustomProviderDialog：渲染 header key 输入；如果没有这行，后端无法保存 header 名。 */}
              <input aria-label="Header Value" placeholder="Header Value" type="password" value={header.value} onChange={(event) => updateHeaderRow(index, "value", event.target.value)} /> {/* 新增代码+CustomProviderDialog：渲染密码型 header value 输入；如果没有这行，敏感 header 值会明文显示。 */}
            </div> // 新增代码+CustomProviderDialog：header 行结束；如果没有这行，JSX 结构不完整。
          ))} {/* 新增代码+CustomProviderDialog：header 行遍历结束；如果没有这行，JSX 表达式不完整。 */}
        </section> {/* 新增代码+CustomProviderDialog：headers 配置区域结束；如果没有这行，JSX 结构不完整。 */}
        {visibleError.length > 0 ? <div className="provider-connect-error" role="alert">{visibleError}</div> : null} {/* 新增代码+CustomProviderDialog：显示本地或后端错误；如果没有这行，校验和保存失败没有可见反馈。 */}
        <div className="provider-connect-actions"> {/* 新增代码+CustomProviderDialog：渲染底部按钮区；如果没有这层，取消和保存按钮无法右对齐。 */}
          <button className="settings-provider-secondary-button" type="button" onClick={resetAndClose}>取消</button> {/* 新增代码+CustomProviderDialog：渲染取消按钮并清理敏感状态；如果没有这行，用户无法放弃添加。 */}
          <button className="settings-provider-primary-button" disabled={pending} type="submit">{pending ? "保存中" : "保存"}</button> {/* 新增代码+CustomProviderDialog：渲染保存按钮；如果没有这行，表单无法提交给后端。 */}
        </div> {/* 新增代码+CustomProviderDialog：底部按钮区结束；如果没有这行，JSX 结构不完整。 */}
      </form> {/* 新增代码+CustomProviderDialog：自定义 provider 表单结束；如果没有这行，JSX 结构不完整。 */}
    </div> // 新增代码+CustomProviderDialog：弹窗遮罩结束；如果没有这行，JSX 结构不完整。
  ); // 新增代码+CustomProviderDialog：返回语句结束；如果没有这行，函数没有返回边界。
} // 新增代码+CustomProviderDialog：函数段结束，CustomProviderDialog 到此结束；如果没有这个边界，用户不容易看出弹窗范围。
