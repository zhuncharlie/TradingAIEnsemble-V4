# 04 — LLM Temporal Integrity

## 1. 目标

Massive 可以提供历史输入，但不能删除 LLM 参数中已学到的未来知识。

每个 LLM adapter 必须获得明确 temporal class，并接受 historical-context firewall 和 leakage audit。

## 2. 分类

```text
STRICT_PIT
EVIDENCE_CONSTRAINED
CURRENT_CONTEXT_ONLY
```

### STRICT_PIT

仅当：

- checkpoint 的知识截止早于测试期，或有充分证据证明不含未来信息；
- 所有外部数据 `published_at <= as_of`；
- 关闭实时网络和搜索；
- 推理过程可审计。

### EVIDENCE_CONSTRAINED

当前模型可能知道未来，但：

- 关闭工具和网络；
- 只提供 Massive 历史 evidence bundle；
- 要求只根据 evidence 回答；
- 每项结论引用 evidence ID；
- evidence 不足时 abstain；
- 保存 prompt、context、output；
- 运行 leakage audit。

不得称为严格 PIT。

### CURRENT_CONTEXT_ONLY

无法可靠历史化的 adapter：

- 仍保留在全 roster；
- 用于工程覆盖、当前上下文或非 claim-bearing case study；
- 不进入严格历史 claim-bearing 结果。

## 3. Historical context firewall

实现：

- 新闻 `published_utc <= as_of`；
- 财务数据使用当时可公开版本；
- 禁止当前网页搜索和实时 analyst snapshot；
- 禁止未来收益、未来价格或 split 名称进入 prompt；
- prompt 明确：

```text
Use only the supplied evidence.
Do not use unstated world knowledge.
Abstain when evidence is insufficient.
```

## 4. Leakage audit

至少设计：

1. 询问 `as_of` 之后事件；
2. evidence 故意省略未来事实；
3. 明确的 sentinel cases；
4. 无 evidence 时的 abstention；
5. 相同 evidence 不同时间标签的一致性测试。

记录：

- adapter；
- model；
- temporal class；
- 是否泄漏；
- 泄漏类型；
- 频率；
- mitigation 效果；
- 是否降级。

生成：

```text
docs/experiment_design/LLM_TEMPORAL_INTEGRITY_PROTOCOL.md
docs/research_reports/LLM_HISTORICAL_KNOWLEDGE_AUDIT.md
```

## 5. 处理原则

- 不删除 LLM adapter；
- 不伪称完全解决；
- 不能通过审计的降级为 `CURRENT_CONTEXT_ONLY`；
- 保留 manifest row；
- claim-bearing 历史分析只使用满足预注册资格的输出。

## 6. 通过条件

- 每个 LLM adapter 有 temporal class；
- firewall 已实现；
- leakage tests 可重复；
- 结果和原始 prompt/context 有审计记录；
- 高泄漏 adapter 已诚实降级。
