# 06 — Experiment Framework

## 1. 进入条件

只有以下条件满足后开始：

- H1 获得 independent PASS；
- H1 implementation spec 冻结；
- Massive provider 验证；
- LLM temporal classes 完成；
- Q4 rolling smoke 通过。

## 2. Common infrastructure

实现：

```text
experiments/common/
```

至少包括：

- config loader；
- adapter roster loader；
- immutable dataset loader；
- split/final-test guard；
- cutoff guard；
- output alignment；
- forward-return labels；
- provenance handling；
- capability/availability/missingness masks；
- result manifest；
- experiment hashes；
- resume；
- failure logging；
- cost/latency tracking。

## 3. Layer 1

实现：

```text
experiments/layer1/
```

模块：

- representation/field value；
- calibration；
- stability；
- generic disagreement；
- structural contradiction；
- cross-Q coherence；
- regime reliability；
- Q4 performance audit；
- Q4 risk/exposure audit；
- H1 dataset；
- H1 primary model；
- robustness。

Layer 1 输出必须能直接作为 Layer 2 输入。

## 4. Layer 2 skeleton

实现：

```text
experiments/layer2/
```

至少可运行：

- majority；
- equal weight；
- raw-confidence weighting；
- calibrated-confidence weighting；
- reliability-aware weighting；
- contradiction-aware intervention；
- abstention；
- shadow Q4；
- routing interface；
- validation-conditioned policy selection；
- meta-fusion interface。

本阶段只要求接口和 baseline 跑通，不做大规模调参。

## 5. 两层关系

```text
Raw adapter outputs
        ↓
Canonical Q1–Q4 + provenance/masks
        ↓                      ↘
Layer 1 reliability features   raw views
        ↓                      ↙
Layer 2 fusion/routing/intervention
        ↓
Final action/ranking/policy
        ↓
Common evaluation
```

Layer 2 必须同时支持：

- raw Q1–Q4 only；
- Layer 1 only；
- raw + Layer 1。

## 6. Schema 边界

以下都属于实验层，不得加入 schema：

- calibration；
- contradiction；
- reliability；
- validation；
- risk metrics；
- returns；
- Sharpe；
- fusion；
- intervention。

## 7. 工程要求

- 配置驱动；
- 同一代码路径可扩展到正式实验；
- 断点续跑；
- 每个结果可追溯到 config、commit、dataset checksum；
- 所有失败进入 manifest；
- 不因 pilot 结果改变 primary metric 或 ontology。
