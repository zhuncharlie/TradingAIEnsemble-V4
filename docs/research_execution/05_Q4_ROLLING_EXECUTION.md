# 05 — Q4 Rolling Execution

## 1. 目标

在实验层统一所有 Q4 adapter 的顺序执行语义，不修改 `CONTRACT/schemas.py`。

建议接口：

```python
initialize(
    context,
    generation_window,
    initial_portfolio_state,
    data_provider,
) -> PolicyRuntime

step(
    runtime,
    timestamp,
    observation,
    portfolio_state,
) -> PolicyDecisionStep

finalize(runtime) -> Q4Policy
```

具体目录可按现有结构做最小调整。

## 2. Policy types

### STATIC_ALLOCATION

仅产生真实静态权重。不得伪造逐日重新决策轨迹。

### ROLLING_OPTIMIZER

每个合法 rebalance point：

- 截断数据；
- 重新 fit/optimize；
- 输出一步；
- 保存输入范围和状态。

### FROZEN_LEARNED_POLICY

只在 generation window 训练或加载。测试期仅推理。

### ONLINE_ADAPTIVE_POLICY

允许按时间更新，但：

- 只使用当前和过去数据；
- 状态跨 step 保存；
- 不允许用完整未来窗口重置或重训。

## 3. 统一语义

必须统一：

- trading calendar；
- rebalance frequency；
- observation cutoff；
- information cutoff；
- execution delay；
- execution price；
- transaction costs；
- slippage；
- CASH；
- missing/failed decision；
- dynamic universe；
- constraints；
- leverage；
- state persistence；
- checkpoint；
- deterministic replay。

## 4. Adapter 状态

每个 Q4 adapter 标记：

```text
NATIVE_STEPWISE
WRAPPED_STEPWISE
STATIC_ONLY
BLOCKED
NOT_APPLICABLE
```

不得因运行慢、算法特殊或字段少而预先删除。

## 5. 测试

必须包含：

- unit tests；
- no-future-data；
- generation/test non-overlap；
- information cutoff；
- state persistence；
- weight sum；
- cash；
- constraints；
- dynamic universe；
- deterministic replay；
- 3-step real smoke；
- short-window rolling smoke。

## 6. 输出

```text
docs/q4_design/Q4_ROLLING_PROTOCOL_FINAL.md
docs/q4_design/Q4_ADAPTER_COMPATIBILITY_FINAL.md
```

## 7. 通过条件

- 所有 Q4 adapter 均有状态；
- 适用 adapter 可通过同一 runner；
- 因果、状态、权重和执行测试通过；
- 无法接入的 adapter 保留为 BLOCKED/STATIC_ONLY；
- transaction cost 和 evaluation 不写回 schema。
