# 09 — Autonomous Execution Policy

## 1. 运行模式

Claude Code 是 lead research engineer，不是每一步都等待批准的顾问。

它必须：

- 按 phase 文件顺序执行；
- 自动处理 Type A；
- 记录 Type B 并继续；
- 仅 Type C 停止；
- 每阶段更新状态但不因更新而停下；
- 长任务使用 tmux/nohup 或现有监控机制；
- 保留日志、manifest 和 resume 信息。

## 2. 不允许的“伪自主”

不得：

- 遇到普通测试失败就停止并询问用户；
- 把每个 minor issue 变成新 session；
- 只写报告不实现；
- 为了“完成”而跳过真实调用；
- 把 blocked adapter 从 roster 静默删除；
- 用 synthetic output 冒充 live result；
- 自动声称 H1 PASS；
- 自动访问 final test。

## 3. 每阶段循环

```text
READ phase plan
    ↓
AUDIT current state
    ↓
IMPLEMENT
    ↓
TEST
    ↓
FIX Type A
    ↓
RECORD Type B
    ↓
UPDATE status + decision log
    ↓
CHECK gate
    ↓
CONTINUE next phase
```

## 4. Session 或上下文结束

在退出前必须更新：

```text
docs/research_execution/EXECUTION_STATUS.md
docs/research_execution/DECISION_LOG.md
```

并写明：

- completed_phase；
- current_phase；
- next_action；
- exact command；
- running process；
- logs；
- blockers；
- git state。

下一次 Claude Code 应从 status 文件恢复，而不是重新理解全部聊天历史。

## 5. 允许的只读 subagents

允许为以下工作 fan out：

- 独立 review；
- 文档核验；
- 只读源码调查；
- 结果审计。

禁止多个 agent 同时修改同一目录或同一文件。

## 6. 停止策略

正常执行只会在以下节点停下：

- Massive OAuth/API key；
- H1 规定轮次后仍非 PASS；
- 必须改 schema/claim；
- 不可逆数据操作；
- aligned pilot 完成。

其余问题必须自行解决、记录或降级后继续。
