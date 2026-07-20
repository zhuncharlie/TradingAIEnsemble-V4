# Research Execution Bundle

本目录把原始长 Prompt 拆成可由 Claude Code 串行执行的阶段文件。

## 文件顺序

1. `00_MASTER_PLAN.md`
2. `01_H1_PROTOCOL_AND_REVIEW.md`
3. `02_ADAPTER_ROSTER_ALIGNMENT.md`
4. `03_MASSIVE_DATA_INFRASTRUCTURE.md`
5. `04_LLM_TEMPORAL_INTEGRITY.md`
6. `05_Q4_ROLLING_EXECUTION.md`
7. `06_EXPERIMENT_FRAMEWORK.md`
8. `07_SMOKE_TESTS_AND_ALIGNED_PILOT.md`
9. `08_FINAL_TEST_FIREWALL_AND_REPORTING.md`
10. `09_AUTONOMOUS_EXECUTION_POLICY.md`

辅助文件：

- `START_CLAUDE_CODE_PROMPT.md`：首次启动 Claude Code 时直接粘贴。
- `EXECUTION_STATUS_TEMPLATE.md`：Claude 每个阶段更新一次。
- `DECISION_LOG_TEMPLATE.md`：记录自动做出的决策和未解决问题。

## 放置位置

建议把整个目录复制到项目仓库：

```text
docs/research_execution/
```

最终结构：

```text
docs/research_execution/
├── README.md
├── 00_MASTER_PLAN.md
├── 01_H1_PROTOCOL_AND_REVIEW.md
├── 02_ADAPTER_ROSTER_ALIGNMENT.md
├── 03_MASSIVE_DATA_INFRASTRUCTURE.md
├── 04_LLM_TEMPORAL_INTEGRITY.md
├── 05_Q4_ROLLING_EXECUTION.md
├── 06_EXPERIMENT_FRAMEWORK.md
├── 07_SMOKE_TESTS_AND_ALIGNED_PILOT.md
├── 08_FINAL_TEST_FIREWALL_AND_REPORTING.md
├── 09_AUTONOMOUS_EXECUTION_POLICY.md
├── START_CLAUDE_CODE_PROMPT.md
├── EXECUTION_STATUS.md
└── DECISION_LOG.md
```

## 使用方式

Claude Code 只需要接收 `START_CLAUDE_CODE_PROMPT.md` 中的短 Prompt。之后它应按照
`00_MASTER_PLAN.md` 和各阶段文件顺序执行，并把状态写入 `EXECUTION_STATUS.md`。

正常情况下不要在每个阶段停下来征求人工批准。只有遇到以下事项才停止：

- Massive OAuth 或密钥需要用户操作；
- 必须修改 `CONTRACT/schemas.py`；
- 必须改变 H1 的核心科学主张；
- 需要删除、覆盖或不可逆迁移大量数据；
- H1 在允许的独立复审轮次后仍无法通过；
- 发生无法恢复的外部服务或凭证阻塞。

Pilot 完成后停止。禁止自动访问 untouched final test、自动运行正式大规模实验或自动投稿。
