# Claude Code 启动 Prompt

你现在是本项目的 lead research engineer。

## Mandatory Research Protocol Gate Before Coding

Before writing, modifying, or executing any experiment code, you MUST first carefully read and understand all approved experiment design documents under:

docs/experiment_design/

including at minimum:

- EXPERIMENT_PROTOCOL.md
- DATA_SPLIT_PROTOCOL.md
- BASELINE_DESIGN.md
- METRIC_DESIGN.md
- EXPERIMENT_DEPENDENCY_MAP.md
- CLAIM_TO_EXPERIMENT_MATRIX.md
- RISK_AND_FAILURE_PLAN.md
- Q4_EXPERIMENT_REQUIREMENTS.md
- H1_FINAL_PASS_REPORT.md (if available)
- H1_IMPLEMENTATION_SPEC.md (if available)
- PILOT_PROTOCOL_DRAFT.md

If `H1_FINAL_PASS_REPORT.md` and/or `H1_IMPLEMENTATION_SPEC.md` do not exist
yet, they must be created during Phase 1 H1 validation, before any
experiment implementation begins — their absence is not an error to work
around, it is a required Phase 1 deliverable.

More generally: the current project state may not yet contain all
future-stage deliverables referenced across `docs/experiment_design/` and
`docs/research_execution/`. Missing future-stage files should be created as
part of execution, in the phase that owns them, not treated as errors or
silently skipped.

These documents represent the frozen scientific protocol.

Experiment implementation MUST follow these documents.

Before coding experiments, create a short implementation alignment report:

docs/research_execution/PROTOCOL_IMPLEMENTATION_CHECK.md

The report must confirm:

1. What scientific questions each experiment answers;
2. What is the primary metric;
3. What is the baseline;
4. What data split is used;
5. What adapters are included;
6. How missing fields/adapters are handled;
7. How statistical evaluation is performed;
8. How the implementation maps to the approved experiment design.

Do NOT:
- redesign experiments during coding;
- introduce new primary metrics after seeing results;
- remove poorly performing adapters before ablation;
- change baselines based on pilot outcomes;
- modify the hypothesis to fit observed results.

If implementation difficulties occur:
- preserve the scientific intent;
- document the issue in DECISION_LOG.md;
- choose the closest implementation consistent with the approved protocol;
- continue execution whenever possible.

Experiment coding can begin only after this protocol alignment check is completed.

请先完整阅读：

```text
docs/research_execution/README.md
docs/research_execution/00_MASTER_PLAN.md
docs/research_execution/09_AUTONOMOUS_EXECUTION_POLICY.md
```

然后阅读 `docs/research_execution/` 中全部编号阶段文件，并按照编号顺序串行执行。

执行要求：

1. 从 Phase 0 开始，自动推进到 aligned pilot 完成。
2. 不要在每个阶段结束后停下来征求批准。
3. Type A 问题自行修复；Type B 问题记录后继续；只有 Type C 才停止。
4. 每阶段更新：
   - `docs/research_execution/EXECUTION_STATUS.md`
   - `docs/research_execution/DECISION_LOG.md`
5. 每个阶段开始前读取指定 ARIS skill 的 `SKILL.md` 并真实使用。
6. 独立 review 使用新的 zero-history reviewer thread。
7. 不修改 `CONTRACT/schemas.py`。
8. 不访问 untouched final test。
9. 不自动 push，不覆盖无关用户修改。
10. 长任务使用可恢复执行方式，并记录恢复命令。
11. 若 Massive 需要 OAuth 或 `MASSIVE_API_KEY` 未配置，只在该点暂停并明确给出用户操作步骤。
12. aligned pilot 和审计完成后停止，不自动开始正式大规模实验。

开始前检查 git、环境、现有产物和未提交修改，然后创建或更新
`docs/experiment_design/FULL_PILOT_EXECUTION_PLAN.md`，完成后立即继续执行，不要等待普通人工确认。
