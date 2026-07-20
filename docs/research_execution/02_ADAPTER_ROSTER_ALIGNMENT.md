# 02 — Full Adapter Roster Alignment

## 1. 目标

不再把 Star 数量作为主实验硬门槛。尽可能让全部 production adapters 进入统一 roster。

adapter 是否有增量价值，由后续 ablation 和结果审计决定，不在实验前凭主观偏好删除。

## 2. 统一 roster

建立：

```text
configs/adapter_sets/all_adapters_aligned.yaml
```

默认包含全部 production adapters。

不得仅因以下原因删除：

- Star 少；
- 运行慢；
- API 昂贵；
- 只支持一个 Q；
- 字段稀疏；
- 输出为 DERIVED；
- 方法与其他 adapter 相似；
- timeout 需要提高。

## 3. 必须保留的掩码与来源

### capability mask

表示 adapter 理论上支持哪些 Q 和字段。

### field provenance

至少区分：

```text
NATIVE
DERIVED
HARNESS_SUPPLIED
MISSING
```

### adapter availability mask

表示某个 `(adapter, as_of, task)` 实际是否成功产生结果。

### Q availability mask

表示该次运行实际产生了 Q1/Q2/Q3/Q4 中哪些层。

### missingness indicators

把缺失本身作为可观察特征，防止模型把“缺失”误当成 HOLD、零风险或零信号。

## 4. blocked 和 failed

对每个失败 adapter：

1. 尝试真实 remediation；
2. 记录失败类别；
3. 尝试修复环境、timeout、credential 路径、数据接口或 adapter bug；
4. 无法恢复时仍留在 roster 和 manifest。

允许状态：

```text
COMPUTED
BLOCKED
FAILED
INELIGIBLE_FOR_THIS_TASK
NOT_APPLICABLE
MISSING_Q
```

不得静默从分母删除。

## 5. Pilot 与正式实验

Pilot 和正式实验使用同一：

- adapter roster；
- registry；
- provider；
- alignment；
- ontology；
- Q4 runner；
- metrics；
- manifest；
-代码路径。

Pilot 只缩小：

- 日期范围；
- universe；
-重复次数；
-训练预算；
-搜索预算；
-数据粒度；
-计算规模。

更新旧的 `pilot_core`、`controlled_scientific_core`、`paper_core` 等集合为 legacy/deprecated alias，或者清楚记录旧含义。新的默认集合为 `all_adapters_aligned`。

## 6. 输出

```text
docs/adapter_management/FULL_ROSTER_ALIGNMENT_REPORT.md
configs/adapter_sets/all_adapters_aligned.yaml
```

报告必须列出：

- 全部 adapter；
- capability；
- provenance；
- live/PIT 状态；
- remediation；
- 当前 pilot 状态；
- manifest 状态；
- 未解决限制；
- 不同 Q 和字段的覆盖率。

## 7. 通过条件

- 全部 production adapters 在 roster 中；
- 每个 adapter 有明确状态；
- 没有伪造缺失；
- registry 可被实验代码机器读取；
- pilot 与正式实验不再使用不同的隐藏名单。
