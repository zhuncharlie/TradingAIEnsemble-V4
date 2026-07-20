# 08 — Final-Test Firewall, Budget, and Reporting

## 1. Final test 定义

Untouched final test 是完全不用于：

- calibrator；
- threshold；
- feature selection；
- model selection；
- baseline selection；
- hyperparameter tuning；
-论文方向选择；

的最终时间区间。

## 2. 防火墙

代码必须实现：

- final-test split 独立配置；
- 默认不可读取；
- 显式 human approval token；
- 访问 audit log；
- pilot 不能通过路径猜测访问；
- 数据和 manifest 隔离；
- 任何读取都记录 commit、config、时间和操作者。

## 3. 未来解锁条件

只有未来全部满足：

1. H1 PASS；
2. pilot 完成；
3. Layer 1 feature freeze；
4. Layer 2 method freeze；
5. baseline freeze；
6. human approval；

才运行一次。

当前任务无论结果如何都不得访问 final test。

## 4. 成本政策

允许较高 API 成本、算力和运行时间，但必须记录：

- API cost；
- LLM token cost；
- GPU/CPU 时间；
- 下载量；
- 缓存命中；
- timeout；
-失败重试；
-预算异常。

高预算不等于无限循环。必须设置最大重试、超时和断点恢复。

## 5. 最终报告

Pilot 完成时终端和 Markdown 总结必须回答：

1. H1 review 轮次和 verdict；
2. H1 primary unit、C、E、confidence、disagreement 和模型；
3. adapter computed/blocked/failed/not applicable 数量；
4. remediation；
5. Massive 连接、权益、历史范围；
6. yfinance 是否退出默认路径；
7. LLM temporal class 和 leakage audit；
8. Q4 rolling support 和因果测试；
9. 实验模块；
10. smoke tests；
11. aligned pilot；
12. schema 字段覆盖；
13. 成本与失败；
14. 正式实验 readiness；
15. 仍需人工决定事项；
16. final test 为何未访问。

停止在 aligned pilot 和审计完成处。
