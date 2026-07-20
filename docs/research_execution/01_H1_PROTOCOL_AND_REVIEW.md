# 01 — H1 Protocol and Independent Review

## 1. 目标

把 H1 从当前 `REVISE` 状态推进到一个：

- 唯一可实现；
- 无内部矛盾；
- 可预注册；
- 可被另一个工程人员等价复现；
- 获得独立 reviewer 诚实 `PASS`；

的规格。

当前已知问题：

- tuple-level unit 未完全传播；
- confidence aggregation 未固定；
- tuple-level 与 adapter-pair effect 的关系不明确；
- 不同实现者可能生成不同 H1 主模型。

## 2. 必须生成

```text
docs/experiment_design/H1_IMPLEMENTATION_SPEC.md
docs/experiment_design/H1_REVIEW_HISTORY.md
docs/experiment_design/H1_FINAL_PASS_REPORT.md
```

同时修复所有受影响的实验协议文件。

## 3. Primary unit of analysis

优先使用：

```text
(asset_or_portfolio_scope, as_of, horizon)
```

一行代表同一资产或组合范围、同一决策时点和同一 horizon 的统一 tuple。

该 tuple 聚合当时所有合格 adapter 的 Q1–Q4 输出。不得因为 adapter pair 数量不同而复制成大量看似独立的样本。

adapter-pair-level 分析可保留为 secondary robustness，不得与 primary model 混写。

## 4. Primary contradiction exposure

主暴露固定为：

```text
C_any ∈ {0, 1}
```

表示 tuple 是否触发预注册 ontology 中至少一种结构性矛盾。

同时保存但仅用于 secondary/exploratory：

```text
C_directional
C_risk
C_cross_q
C_policy
contradiction_class_count
contradiction_breadth
contradiction_persistence
```

不得根据 pilot 结果把最显著的 variant 改成 primary。

## 5. Confidence representation

每个 tuple 至少记录：

```text
mean_confidence
median_confidence
max_confidence
min_confidence
confidence_dispersion
high_confidence_conflict
confidence_kind_counts
confidence_missing_rate
```

主模型必须提前固定实际使用的 confidence covariates。

不得把 `PROBABILITY`、`SELF_REPORTED`、`MODEL_MARGIN`、
`SCORE_NORMALIZED`、`ENTROPY_DERIVED` 和 `HEURISTIC` 无条件视为同一种概率。

## 6. Generic disagreement

固定一个 primary generic-disagreement control，优先：

```text
normalized directional vote entropy
```

其他 dispersion、pairwise disagreement 或距离只能作为 robustness。

目的：证明 structural contradiction 不是普通分歧的同义词。

## 7. Missingness and composition

每个 tuple 必须记录：

```text
eligible_adapter_count
available_q1_count
available_q2_count
available_q3_count
available_q4_count
adapter_availability_mask
q_availability_mask
paradigm_counts
```

缺失必须保留为真实观察，不得用默认 HOLD、默认 confidence、零权重或模板 reasoning 填补。

## 8. Outcome E

预测和 policy outcome 必须分开。

### H1-Forecast

候选 outcome：

- Q1/Q3 后续方向错误；
- 连续方向损失；
- adapter 级损失聚合后的 tuple-level 预测质量。

必须明确 HOLD、NEUTRAL、缺失和相互冲突的多 adapter 输出如何处理。

### H1-Policy

候选 outcome：

- Q4 相对同 universe benchmark 的未来净损失；
- 加入统一交易成本后的相对退化。

必须明确静态策略、rolling 策略、无仓位和失败 step 的处理。

### Primary 与 secondary

必须在 review 前固定：

- 哪一个是 primary claim-bearing outcome；
- 哪一个是 secondary / external-validity track；
- tuple 内多个 adapter 损失如何聚合；
- 交易成本何时进入；
- 缺失如何进入分析。

## 9. Primary statistical model

写死一个唯一主规格：

- model type；
- outcome；
- exposure；
- covariates；
- interactions；
- random/fixed effects；
- time dependence；
- clustered 或 block-bootstrap inference；
- significance threshold；
- practical effect size；
- falsification conditions。

若采用 tuple-level 主模型，解释：

- adapter pair 为何不再是主样本行；
- 如何用 adapter composition、availability mask 和 coverage 控制组成差异；
- pair-level 模型如何作为 secondary robustness。

不得在看到结果后从多个主模型中挑最显著的一个。

## 10. Robustness

至少固定：

- leave-one-adapter-out；
- leave-one-ticker-out；
- leave-one-paradigm-out；
- 1d/5d/20d breakdown；
- regime breakdown；
- alternative disagreement control；
- pair-level secondary model；
- block bootstrap；
- multiple-comparison correction。

## 11. Review loop

1. 完成 implementation spec。
2. 使用 zero-history reviewer。
3. reviewer 输出 `PASS / REVISE / FAIL`。
4. `REVISE` 时只修复明确的逻辑、可实现性或一致性问题。
5. 使用新的 reviewer thread 复审。
6. 最多新增五轮。

禁止：

- 削弱 H1；
- 删除 falsification criteria；
- 把 pooled primary test 改成挑显著 stratum；
- 用模糊措辞获取 PASS；
- 把 self-review 冒充 independent review。

若五轮后仍非 PASS，记录不可解决的 scientific blocker，并作为 Type C 停止。

## 12. Gate A

只有以下条件全部成立才进入 Phase 2：

- `H1_IMPLEMENTATION_SPEC.md` 完整；
- 相关协议同步；
- 独立 reviewer `PASS`；
- `H1_FINAL_PASS_REPORT.md` 记录 thread、理由和最终规格；
- final test 仍未访问。
