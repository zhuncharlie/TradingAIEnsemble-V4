# 07 — Smoke Tests and Aligned Pilot

## 1. Smoke tests

先使用：

- fixtures；
- 已保存的真实 adapter JSON；
- Massive 小样本；
- 人工构造 contradiction cases。

验证：

1. 全部 production adapters 在 roster；
2. 所有 adapter 被尝试；
3. 缺失不被伪造；
4. Q1–Q4 对齐；
5. 1d/5d/20d 标签；
6. embargo；
7. final-test guard；
8. `C_any`；
9. fixed disagreement；
10. tuple 唯一性；
11. composition/masks；
12. Massive 复现；
13. LLM firewall；
14. Q4 rolling 因果；
15. manifest 状态。

运行：

- unit tests；
- integration tests；
- one-date smoke；
- three-date smoke；
- short-window smoke；
- 每个 adapter 最小 live smoke。

输出：

```text
docs/research_reports/EXPERIMENT_CODE_SMOKE_REPORT.md
results/smoke/manifest.jsonl
```

所有失败必须保留。

## 2. Aligned pilot 原则

Pilot 与正式实验使用相同：

- roster；
- provider；
- alignment；
- ontology；
- Q4 runner；
- metrics；
- manifest；
- model specification；
-代码路径。

Pilot 只缩小：

- 日期跨度；
- universe；
- repeats；
-训练预算；
-搜索预算；
-数据粒度；
-计算规模。

## 3. Pilot roster

使用：

```text
configs/adapter_sets/all_adapters_aligned.yaml
```

不得只运行容易成功的 adapter。每个 adapter 都必须有 manifest row。

## 4. Pilot scope

优先：

- 1d、5d；
- 样本允许时加入 20d；
- 小型但多样化 equity universe；
- calibration + validation；
- final test 锁定；
- LLM 重复运行；
- Q4 统一 rolling。

## 5. Pilot 目标

验证：

- roster 可运行性；
- schema 字段覆盖；
- aligned tuple 数量；
- contradiction incidence 和类别样本量；
- confidence-kind；
- missingness；
- H1 可识别性；
- block bootstrap；
- leave-one-out；
- Q4 一致性；
- 成本和时间；
- remediation；
- 正式实验规模需求。

Pilot 不以“显著”作为工程成功条件。

## 6. Pilot 后禁止

不得根据 pilot：

- 修改 final test；
- 扩大/缩小 H1 ontology；
- 删除表现差 adapter；
- 挑最佳 seed；
- 改 primary metric；
- 改主模型以追求显著。

adapter removal 只能在预注册 ablation 中研究。

## 7. 结果审计

使用：

```text
analyze-results
experiment-audit
result-to-claim
```

生成：

```text
docs/experiment_design/ALIGNED_PILOT_PROTOCOL.md
configs/experiments/aligned_pilot.yaml
docs/research_reports/ALIGNED_PILOT_REPORT.md
docs/research_reports/ALIGNED_PILOT_EXPERIMENT_AUDIT.md
docs/research_reports/ALIGNED_PILOT_RESULT_TO_CLAIM.md
results/pilot/manifest.jsonl
```

## 8. Gate C

Pilot 完成后判断：

- 是否具备正式实验数据规模；
- 哪些 adapter 需要 remediation；
- 哪些结果只能 diagnostic；
- H1 是否可识别；
- Layer 2 哪些路线值得正式 validation；
- 预算和运行时间。

然后停止，等待人工批准正式实验。
