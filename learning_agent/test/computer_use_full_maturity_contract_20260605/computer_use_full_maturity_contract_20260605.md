# /computer use --full 成熟契约记录

日期：2026-06-05

目标：冻结 `/computer use --full` 的成熟版产品边界，避免继续无止境追加 Phase。

本轮结论：
- `/computer use --full` 表示“用户明确确认后的通用受控桌面模式”，不是无限权限。
- 成熟版必须走单一通用 runtime，不允许回到每个应用一个 controller。
- 普通应用不应依赖硬编码白名单或逐应用补丁。
- 高风险目标、凭据窗口、系统设置、终端、管理员工具仍必须默认拒绝。
- 最终成熟声明必须经过真实可见终端验收，单元测试不能替代。

新增代码：
- `learning_agent/computer_use/full_maturity_contract.py`
- `learning_agent/tests/test_windows_computer_use_full_maturity_contract.py`

红测证据：
- 先运行 `python -m unittest learning_agent.tests.test_windows_computer_use_full_maturity_contract`
- 结果为 `ModuleNotFoundError: No module named 'learning_agent.computer_use.full_maturity_contract'`
- 这证明测试先于实现，缺口是真实存在的。

固定 token：
- `COMPUTER_USE_FULL_MATURE_READY`
- `COMPUTER_USE_FULL_MATURE_OK`

后续约束：
- 后续 Generic Launch、Target Identity、Cleanup、Action Loop、Final Matrix 都必须引用或遵守该契约。
