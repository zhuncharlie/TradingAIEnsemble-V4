# 00 — Master Execution Plan

## 1. 总目标

把项目从“实验协议已设计，但尚未形成统一可执行实验”推进到：

1. H1 形成唯一、可实现、通过独立审查的规格；
2. 全部 production adapters 尽可能进入统一 roster；
3. Massive 成为默认历史数据源；
4. LLM 历史知识风险得到分类、约束和审计；
5. Q4 rolling execution 在实验层统一；
6. Layer 1、Layer 2 和公共实验代码完成；
7. smoke tests 完成；
8. aligned pilot 完成并接受实验审计；
9. 在 pilot 完成处停止，保持 final test 未访问。

目标会议：ACM ICAIF。

## 2. 不可违反的规则

- 不访问 untouched final test。
- 不使用 final test 调参。
- 不伪造缺失 adapter 输出、confidence、reasoning、Q 层或权重。
- 不静默排除失败或 blocked adapter。
- 不为了获得显著结果削弱 H1、改变 ontology 或挑选显著分层。
- 不修改 `CONTRACT/schemas.py`。
- 不把 pilot 结果描述为正式论文最终证据。
- 不自动 push；除非用户明确要求，不修改远程配置。
- 不覆盖与当前任务无关的用户修改。
- 旧实验结果可以被标记 deprecated，但不得无记录删除。

## 3. 串行阶段

```text
Phase 0  初始检查与执行计划
    ↓
Phase 1  H1 规格与独立 review
    ↓  Gate A: honest PASS
Phase 2  全 adapter roster 对齐
    ↓
Phase 3  Massive 数据基础设施
    ↓
Phase 4  LLM temporal integrity
    ↓
Phase 5  Q4 rolling execution
    ↓  Gate B: 数据、LLM、Q4 smoke 均通过
Phase 6  实验代码
    ↓
Phase 7  smoke tests
    ↓  Gate C: smoke 可接受
Phase 8  aligned pilot + audit
    ↓
停止；等待人工决定是否进入正式实验
```

不得并行运行会修改同一文件的多个 agent。允许使用只读 reviewer 或只读 subagent，但主 agent 必须统一合并结果。

## 4. 开始时必须执行

1. 阅读 `CLAUDE.md`。
2. 检查 branch、commit、git status 和未提交文件。
3. 阅读本目录全部计划文件。
4. 阅读 `docs/research_positioning/`、`docs/experiment_design/`、
   `docs/adapter_management/`、registry、schema、harness 和 adapter 报告。
5. 建立或更新：
   - `docs/research_execution/EXECUTION_STATUS.md`
   - `docs/research_execution/DECISION_LOG.md`
   - `docs/experiment_design/FULL_PILOT_EXECUTION_PLAN.md`
6. 在执行计划中记录预计修改目录、依赖、成本、风险和人工操作点。
7. 计划完成后自动继续，不要仅因为发现普通问题而停下。

## 5. ARIS Skills

开始每个阶段前读取相关 `SKILL.md`。

### H1 和审查

```text
kill-argument
research-review
research-refine
result-to-claim
experiment-audit
```

### 设计与实现

```text
experiment-plan
experiment-bridge
system-profile
ablation-planner
```

### 运行与结果

```text
experiment-queue
run-experiment
monitor-experiment
training-check
analyze-results
experiment-audit
result-to-claim
```

每次独立 reviewer 必须使用新的 thread，不得透露上一轮 verdict、作者希望获得 PASS，或旧 reviewer 的详细意见。

## 6. 阻塞分类

### Type A：自动修复并继续

包括：

- 文档冲突；
- 测试失败；
- timeout；
- 缓存、路径、序列化、环境等工程问题；
- 可通过局部代码修复的 adapter 或 provider bug；
- 缺失报告或 manifest；
- 指标实现与协议不一致。

记录到 `DECISION_LOG.md`，修复并继续。

### Type B：记录状态并继续

包括：

- adapter 不支持某个 Q；
- 当前任务不适用；
- 某 adapter 只能 CURRENT_CONTEXT_ONLY；
- 外部 API 暂时失败但其他阶段可继续；
- 某字段永久缺失；
- 某 adapter 只能 STATIC_ONLY；
- 某结果样本不足但不影响基础设施开发。

在 manifest 中标记 `BLOCKED`、`FAILED`、`NOT_APPLICABLE`、
`INELIGIBLE_FOR_THIS_TASK` 或 `MISSING_Q`，不要静默删除。

### Type C：必须停止并请求人工操作

仅限：

- Massive OAuth 或密钥需要用户操作；
- 必须修改 `CONTRACT/schemas.py`；
- 必须改变 H1 的核心科学 claim；
- 需要不可逆删除或覆盖大量数据；
- 需要新增付费 credential；
- H1 在规定轮次后仍无法获得诚实 PASS；
- 外部服务完全不可用且使后续所有阶段失去输入。

## 7. 恢复机制

每完成一个阶段都更新 `EXECUTION_STATUS.md`，但不要因此停下来。

状态至少记录：

- 当前阶段；
- 已完成产物；
- 测试结果；
- 未解决 Type B 问题；
- 下一阶段；
- 恢复命令；
- 当前 git commit/status；
- 运行中的 tmux/nohup 任务；
- 数据和结果 manifest 路径。

若上下文 compact、Claude session 结束或机器重启，下一次只需读取：

```text
docs/research_execution/00_MASTER_PLAN.md
docs/research_execution/EXECUTION_STATUS.md
docs/research_execution/DECISION_LOG.md
```

然后从 `next_action` 继续。

## 8. 最终停止点

aligned pilot 及其以下报告完成后停止：

- pilot report；
- experiment audit；
- result-to-claim；
- 成本与失败总结；
- 正式实验 readiness 判断。

不得自动：

- 解锁 final test；
- 运行正式大规模实验；
- 根据 pilot 改动 primary ontology 或 primary metric；
- 自动投稿。
