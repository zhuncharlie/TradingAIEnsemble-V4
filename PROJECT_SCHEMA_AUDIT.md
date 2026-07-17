# PROJECT_SCHEMA_AUDIT — 原始能力 / Schema 字段 / Adapter 接入可行性 初步审计

生成日期：2026-07-17
审计范围：CONTRACT/schemas.py v2.0.0（Q1 Action / Q2 State / Q3 Signal / Q4 Policy，无 Q5）
性质：**仅调查与报告**。本文档及配套 `PROJECT_SCHEMA_AUDIT.csv` 未修改任何生产代码、adapter 或 `CONTRACT/schemas.py`。

---

## 一、执行摘要

本次审计覆盖 **27 个项目**：用户指定的 20 个候选 GitHub 项目，加上本仓库 `adapters/*.py` 中已经真实接入、但上游不在候选清单内的 7 个 adapter（atlas / nofx / finclaw / deepalpha / agentictrading / prediction_arena / vibe_trading）。所有项目均通过真实代码阅读完成（而非仅读 README），6 组并行调查各自产出了逐项目深度分析、Q1–Q4 字段级映射表、信息保留度估算与 CSV 行。

**主要结论：**

1. **没有任何单一项目能同时覆盖 Q1–Q4**。项目天然按能力形态聚类：LLM/多智能体项目（TradingAgents、ai-hedge-fund、FinMem、FinAgent、FinRobot）强于 Q1/Q2；因子挖掘项目（Qlib、RD-Agent、AlphaGen、AlphaForge、Alpha-GFN、atlas、finclaw、deepalpha）强于 Q3；组合优化/RL 项目（FinRL、FinRL-Trading、EarnMore、PGPortfolio、TradeMaster、skfolio、Universal Portfolios、DeepDow）强于 Q4。
2. **v2 schema 的"可选字段+开放词汇"设计已被验证是必要的**：几乎每个项目都在至少一个字段上呈现 `MISSING` 或 `NOT_APPLICABLE`，如果 v1 式的"强制必填"仍然存在，这些真实、诚实的差距会被伪造数据掩盖。
3. **发现两类值得注意的问题，而非仅仅是覆盖率数字：**
   - **信息主动丢弃（不是不存在，而是当前 adapter 代码没有读取）**：`ai-hedge-fund` 的 `PortfolioDecision.quantity` 被现有 v1 adapter 完全丢弃；`finclaw` 的完整 74 字段 `StrategyDNA`（一个真实的可执行策略基因组）从未被读取为 Q4 policy；`vibe_trading` 的完整逐日 `positions.csv` 轨迹和真实订单历史只读取了最后一行；`agentictrading` 的真实 mean-variance/equal-weight 权重从未被提取；`Qlib` 自带的 `TopkDropoutStrategy`/`WeightStrategyBase`/`backtest` 引擎完全未被使用；`AlphaForge`/`RD-Agent` 的中间因子池权重与每日生效因子子集只存在于内存中，从未持久化。
   - **字段-语义错配（现有代码把信息放错了 Q 层）**：`FinRL-Trading` 的真实市场 regime 探测器（`RISK_ON/NEUTRAL/RISK_OFF` + `risk_score` + `cash_floor`）目前被 v1 adapter 塞进 Q4 的 `regime` 字段，而 v2 schema 明确设计为 regime 应属于 Q2 的开放 `StateEstimate`，不属于 Q4——这是一个具体的、需要在 v1→v2 迁移时修正的错配，而不是新发现的能力缺口。
4. **Q5（回测）在 v2 中确实已经不再适用**：`agentictrading`、`FinRL`（旧版）、`prediction_arena`、`vibe_trading`、`TradeMaster`、`FinRobot` 等项目内部都有真实的回测/绩效计算代码（Sharpe、drawdown、return），但按用户明确指示，这些一律标记为超出范围（out-of-scope），不计入任何 Q1–Q4 覆盖率或信息保留度。
5. **Schema 候选新增字段：三个 OPTIONAL_EXTENSION 候选**（详见第九节），均不满足"必须加入"门槛（无一违反时间因果或执行完整性），建议留作未来可选扩展，而非本次立即加入。
6. **不建议加入 schema 的能力清单较长**（详见第十节）：包括所有回测/评价指标，以及多个仅出现在单一项目中的特有实现细节（如 AlphaForge 的日度因子集成权重结构、TradeMaster DeepTrader 的丢弃中间打分张量等）。

---

## 二、调查方法和评分方法

### 调查方式
6 组并行深度调查（每组 4–7 个项目），每组均：
- 直接阅读真实源码（入口脚本、核心模型/agent 类、数据输入与预处理、推理/决策/policy 流程、返回值与保存的文件、示例与配置、checkpoint/因子/权重/订单等 artifact），而非仅依赖 README。
- 已有本地 `adapters/vendor/` 克隆和现有（v1 schema）adapter 代码的项目（TradingAgents、ai-hedge-fund、FinGPT、Qlib、RD-Agent、AlphaGen、FinRL、FinRL-Trading，以及 7 个不在候选清单内的本地 adapter）以本地代码为主要来源，辅以 `git log -1` 核实 commit、`DECISIONS.md` 核实原始选型理由，但仍独立重新核对，不直接照抄 v1 字段名。
- 无本地克隆的项目（FinBERT、FinRobot、FinMem、FinAgent、AlphaForge、Alpha-GFN、TradeMaster、skfolio、EarnMore、PGPortfolio、DeepDow、Universal Portfolios）通过 `git clone --depth 1` 到独立 scratch 目录 + 直接读取源码文件完成，不进行任何长时间训练、不下载大型数据集、不调用付费 API。
- 记录每个项目的 GitHub URL、分支、commit hash、commit 日期、论文链接、是否为论文官方实现（并说明判定依据）。

### 评分方法（严格按用户既定规则执行）
- **字段状态**：`NATIVE`（真实代码直接输出）/ `DERIVED`（可从真实输出可靠推导）/ `HARNESS_SUPPLIED`（由统一任务上下文提供）/ `MISSING`（不能可靠获得）/ `NOT_APPLICABLE`（该项目能力形态不适用此字段）。
- **信息保留度打分**：无损进入 canonical 字段 = 1.0；可确定性推导只有轻微转换 = 0.8；经归一化/压缩/语义合并后部分保留 = 0.5；canonical schema 完全没有表示 = 0.0。核心决策输出权重 = 2，解释/证据/辅助元数据权重 = 1。`Information Retention = 加权保留分数 / 原生输出总权重`。
- **禁止事项**（全程遵守）：不生成模板化 reasoning；不默认 confidence=0.5；不将任意分数强行解释为概率；不将回测动作误标为预测信号；不将单点权重误描述为完整 policy；不把 README 宣称但代码未实现的能力标记为 NATIVE。
- **Adapter Effort**：`LOW / MEDIUM / HIGH / BLOCKED`。**Priority**：`P0 / P1 / P2 / REJECT`。

---

## 三、项目身份与论文核验（总表）

| Project | GitHub | Commit | Paper | 官方实现？ |
|---|---|---|---|---|
| TradingAgents | TauricResearch/TradingAgents | 85946c2f | arXiv:2412.20138 | 是（同一作者组织） |
| ai-hedge-fund | virattt/ai-hedge-fund | 65a0349c | 无 | n/a（软件项目，非论文） |
| FinGPT | AI4Finance-Foundation/FinGPT | 608a4967 | arXiv:2306.06031 等系列 | 是 |
| Qlib | microsoft/qlib | d5379c52 | arXiv:2009.11189 | 是 |
| RD-Agent | microsoft/RD-Agent | 4f9ecb00 | arXiv:2505.15155（R&D-Agent-Quant）+ 2505.14738 | 是 |
| AlphaGen | ICT-FinD-Lab/alphagen | 259687e8 | arXiv:2306.12964（KDD 2023） | 是 |
| FinRL | AI4Finance-Foundation/FinRL | 220f9e49 | arXiv:2011.09607 | 是 |
| FinRL-Trading (FinRL-X) | AI4Finance-Foundation/FinRL-Trading | e65d6f04 | arXiv:2603.21330 | 是 |
| FinBERT | ProsusAI/finBERT | 44995e0c | arXiv:1908.10063 | 是 |
| FinRobot | AI4Finance-Foundation/FinRobot | 297a8d28 | arXiv:2405.14767 | 是 |
| FinMem | pipiku915/FinMem-LLM-StockTrading | be814aa4 | arXiv:2311.13743（AAAI/ICLR workshop） | 是 |
| FinAgent | DVampire/FinAgent | 17248a0b | arXiv:2402.18485（**概率性认定，非确证**——见证据缺口） | 概率性是 |
| AlphaForge | DulyHao/AlphaForge | d0cfc27d | arXiv:2406.18394（AAAI 2025） | 仓库自称，未独立核实论文 code-availability 声明 |
| Alpha-GFN | nshen7/alpha-gfn | b0f415c1 | **无正式论文**（后继工作 AlphaSAGE, arXiv:2509.25055，另有独立仓库 BerkinChen/AlphaSAGE） | 否——demo-only |
| TradeMaster | TradeMaster-NTU/TradeMaster | 1747cc18 | NeurIPS 2023 (Datasets & Benchmarks)，无 arXiv | 很可能是（机构/作者匹配），未独立核实 PDF 声明 |
| skfolio | skfolio/skfolio | 109ed13f | arXiv:2507.04176 | 是（作者即维护者） |
| EarnMore | DVampire/EarnMore | 810ff594 | arXiv:2311.10801（WWW 2024） | 很可能是（自引用匹配） |
| PGPortfolio | ZhengyaoJiang/PGPortfolio | 48cc5a4a | arXiv:1706.10059 | 是（作者自述） |
| DeepDow | jankrepl/deepdow | 384e18ac | **无专属论文**（框架，各层引用各自经典论文） | n/a |
| Universal Portfolios | Marigold/universal-portfolios | deb797be | 无单一论文（Cover 1991 等经典算法合集） | n/a（第三方开源工具箱） |
| atlas（本地）| Yitong-Guo/Genetic-Algorithm-for-quantitative-alpha-factors-mining | 3e18d723 | 无 | n/a |
| nofx（本地，实为 QuantMuse）| 0xemmkty/QuantMuse | f86ede35 | 无 | n/a |
| finclaw（本地）| PyPI `finclaw-ai`（无公开 GitHub 仓库） | n/a | 无 | n/a |
| deepalpha（本地）| LeoRigasaki/stock-market-prediction-engine | ce87a864 | 无 | n/a |
| agentictrading（本地）| Open-Finance-Lab/AgenticTrading | 294e873b | 无 | n/a |
| prediction_arena（本地）| Metaculus/forecasting-tools | e0ee1ffe | arXiv:2604.07355（**该论文未公开代码链接**，非此仓库） | 否——伴生工具，非论文本体 |
| vibe_trading（本地）| HKUDS/Vibe-Trading | 1e7f7fcd | 无 | n/a |

---

## 四、每个项目的详细分析

以下按能力形态分组，每项给出：原理、原生输出（真实代码验证）、适用场景/时间形态/资产范围、运行条件、以及本次审计中发现的关键结构性问题。完整字段级证据见 §六 CSV 或原始 6 组调查记录；此处聚焦"审计发现"而非逐字段重复。

### 4.1 LLM / 多智能体（强 Q1/Q2）

**TradingAgents**——多智能体 LangGraph 辩论框架（分析师团队→多空研究员辩论→风险三方辩论→PM）。`PortfolioDecision.rating`（5 档）、`SentimentReport`（6 档 band + 0-10 score + low/med/high confidence + narrative）、`bull_history`/`bear_history` 均为真实、可直接读取的字段。**无 Q3/Q4 能力**——项目从不产出标量 alpha 或权重向量。风险三方辩论内容目前没有专属字段承接。

**ai-hedge-fund**——13 个"投资人格"LLM agent + 规则化 risk manager + 一次 PM LLM 调用，`PortfolioDecision{action,quantity,confidence,reasoning}` 按 ticker 返回。**关键发现：现有 v1 adapter 读取 `action/confidence/reasoning` 但从未读取真实的 `quantity`（整数股数）字段**——这是一个具体、低成本可修复的 bug，不是 schema 限制。仓库另有一个大部分未完工的 `v2/` 重写（仅 `pead.py` 和 `backtesting/engine.py` 是真代码，`optimizer.py`/`risk/manager.py`/`pipeline/execution.py` 都是 5 行 docstring 空壳），其中 `PEADModel` 提供了一个真实的、point-in-time 纪律良好的 Q3 conviction 信号。

**FinMem**——单 agent + 分层记忆（short/mid/long/reflection）+ guardrails 强制校验的结构化输出。`investment_decision∈{buy,sell,hold}` 与 `summary_reason` 均为 guardrails 强校验的真实字段（非仅 README 宣称）。**`Portfolio` 类完全没有 cash 字段**，只累加 ±1/0 的股数方向，因此 `target_weights` 无法推导——这是仓库本身的真实限制，不是 adapter 映射选择。是三个 LLM-agent 项目中 checkpoint/决策轨迹最完整的一个（`save_checkpoint()` 每步真实落盘）。

**FinAgent**——与 FinMem 同属单 agent + 记忆检索（`DiverseQuery` 向量检索）架构，但**独有优势：`cash`/`position`/`value` 全部在 `info` 中显式追踪**，因此 `target_weights` 可以无损推导——这是三个 LLM-agent 项目中唯一能干净支持 Q4 权重轨迹的。`check_keys=["action","reasoning"]` 由 `backoff` 装饰器强制重试校验，结构化程度高。论文归属为概率性推断（见证据缺口）。

**FinRobot**——AutoGen 工具调用框架，本身不是单一 pipeline。**关键发现（架构性缺陷，非 schema 问题）：所有 shipped demo 的最终"预测/分析"结果只存在于 AutoGen 聊天记录里，`SingleAssistant.chat()` 只打印到控制台并返回 `None`**——没有任何函数返回值捕获这个最有价值的输出。唯一真正原生、可直接拿到的输出是 Trade_Strategist demo 生成并写入磁盘的 BackTrader 策略代码文件（`PolicyArtifact` 候选）。

**FinBERT**——纯监督微调分类器，无 ticker/date 概念，只支持 Q2。三分类标签 + softmax 分布 + `sentiment_score` 全部真实、干净地映射进 `StateEstimate`，是本次审计中信息保留度最高的项目之一（~90%），但这是因为其真实能力面本身就很窄。

### 4.2 因子挖掘 / Alpha 信号（强 Q3）

**Qlib**——Alpha158（158 个预定义因子）+ LightGBM 回归。`predict()` 输出的连续分数本身就是训练标签（`Ref($close,-2)/Ref($close,-1)-1`，即真实的前瞻收益率）的直接预测，是本批信息保留度最高的项目（~85-90%）。**未使用的真实 Q4 能力**：`qlib/contrib/strategy/signal_strategy.py` 的 `TopkDropoutStrategy`/`WeightStrategyBase` 以及完整的 `qlib/backtest/` 执行引擎，可以把预测分数转成真实目标权重/交易决策，但当前任何 adapter 都未接入。

**RD-Agent**——LLM-agent 研发循环（假设生成→公式转换→CoSTEER 代码实现→真实本地执行）。`FactorTask.factor_formulation`（真实公式字符串）、`Hypothesis.hypothesis/.reason`、`HypothesisFeedback` 均为真实字段。Docker 化的 Qlib LGBM 组合回测能力真实存在但当前 adapter 不调用。

**AlphaGen**——真实 PPO 强化学习搜索因子表达式，`LinearAlphaPool.state`（`exprs`/`ics_ret`/`weights`/`best_ic_ret`）字段名与 adapter 读取路径完全一致，已独立核实。

**AlphaForge**——两阶段：GAN 式神经搜索挖掘因子池，再用滚动窗口 OLS 动态组合。**关键限制：AFF 方法本身从不保存 GAN checkpoint**（只在训练早停时用 `deepcopy` 临时保存，训练结束即丢弃），且每日生效因子子集与回归权重只存在内存列表，从未持久化——这些是真实的、可修复的"计算了但丢弃"缺口，而非虚构。无 license 文件。

**Alpha-GFN**——GFlowNet 因子挖掘。**并非任何已发表论文的官方实现**——仓库自身 README 说明这只是作者更完整后继工作（AlphaSAGE, arXiv:2509.25055，独立仓库）之前的、"仅用于演示目的"的демо，且**完全没有 checkpoint 保存/加载代码**，每次调用都要重新训练。仓库自己承认"仅训练了 1000 episode，模型完全没有优化"。`backtest.ipynb` 是空的 TODO 占位符，未实现任何能力。

**atlas / finclaw / deepalpha**（本地已接入）——三个本地 adapter 都干净地覆盖 Q3，`values`/`factor_expression`/`expected_returns` 多为 NATIVE 或轻度 DERIVED。**finclaw 的重大发现**：其真实 74 字段 `StrategyDNA`（含 `hold_days`/`stop_loss_pct`/`take_profit_pct`/`max_positions` 等）是一个完整的、可序列化的可执行策略基因组，当前 adapter 完全没有把它暴露为 Q4 policy——这是本次审计发现的最大"存在但未提取"的 Q4 缺口之一。

### 4.3 组合优化 / 强化学习（强 Q4）

**FinRL / FinRL-Trading**——`StockPortfolioEnv.softmax_normalization()` 从代码层面硬保证权重非负且和为 1（`initial_weights`/`constraints.long_only` 均为 NATIVE，非推测）。**FinRL-Trading 是本批 Q3+Q4 综合最丰富的项目**：真实 ML 集成模型排序选股（top-25% 动态资产池，`universe_policy.mode="dynamic"`）+ DRL 权重分配 + 真实规则式 regime 探测器（`RISK_ON/NEUTRAL/RISK_OFF` + `risk_score` + `cash_floor`）。**关键发现（字段错配）：这个 regime 探测器目前被 v1 adapter 塞进 Q4 的 `regime` 字段，但按 v2 schema 自己的设计意图，regime 属于 Q2 的开放 `StateEstimate`，不是 Q4 属性**——迁移时需要拆分成独立的 Q2 输出，而非简单改名。两个项目都存在 `generation_window` 架构缺口：目前由 adapter 自行计算训练窗口，而 v2 contract 要求这应由 harness 提供、adapter 只能记录。

**EarnMore**——真实 masked-SAC 强化学习 + 可定制资产子池（无需重训练即可套用不同 mask）。`infos["portfolios"]`（逐日真实权重）与 `save_checkpoint()` 均为 NATIVE。

**PGPortfolio**——EIIE CNN + 真实滚动重训练（`rolling_train()`），`decide_by_history()` 直接输出真实权重向量。内部 pre-softmax `self.voting` 张量从未通过任何公开 API 暴露，若要作为 Q3 信号需要修改上游源码（不符合"薄封装"要求，标记为 MISSING 而非降级实现）。

**Universal Portfolios**——经典 OLPS 算法集合（UP/ONS/OLMAR/PAMR/Anticor/CORN 等，均真实因果 `step()`）。**关键因果性发现**：`BCRP`/`BestMarkowitz` 是事后诸葛亮式的整段回看最优基准，**绝不能**当作前瞻 policy 使用——审计已明确将其排除在 Q4 policy 映射之外，只有真正逐步因果的算法才计入。

**TradeMaster**——NeurIPS 2023 平台，portfolio_management 子系统有 5 个真实算法变体（base/EIIE/DeepTrader/SARL/Investor-Imitator），`weights_memory`/`.pth`/`.pkl` checkpoint 均为真实公开属性。**约束因算法而异，不可全仓统一声明**：DeepTrader 真实允许做空且无 cash 槽，其余变体强制 long-only+cash。DeepTrader 内部真实计算了逐资产打分张量 `asset_scores` 但 `get_action()` 从不返回它——只能通过脆弱的运行时 monkey-patch 获取，标记为 HIGH effort。

**skfolio**——`arXiv:2507.04176` 论文的官方实现，凸优化组合库。约束参数（`min_weights`/`max_weights`/`budget`/`max_short`/`max_long`/`max_turnover`）与 `PortfolioConstraints` 字段近乎 1:1 直接对应，是本批约束覆盖最干净的项目。**关键警示（rubric 明确点名的陷阱）：单次 `.fit()` 只产生单点静态权重快照，不是完整 policy/trajectory**——必须通过显式组合 `cross_val_predict(estimator, X, cv=WalkForward(...))` 才能获得真正因果滚动的决策轨迹；若 adapter 只调用一次 `.fit()`，有效信息保留度会从 ~75-80% 骤降到 ~40%。

**DeepDow**——差分编程框架（非单一算法），`forward()` 只返回权重张量，是本批 Q3 支持最弱、依赖架构选择（仅 BachelierNet/Thorp 类网络才有可提取的 `exp_rets`/`covmat` 中间张量）的项目。

### 4.4 本地已接入但不在候选清单内的 7 个 adapter

**nofx（实为 QuantMuse）**——Q2 强项（sentiment + risk，均 NATIVE），但真实计算的技术因子字典（`calculate_technical_factors()`）当前完全被丢弃，从未作为 Q3 输出暴露。

**agentictrading（AgenticTrading）**——当前只回答已废弃的 Q5；但仓库内部真实存在 `mean_variance.py::_optimal_weights()`（真实 long-only max-Sharpe 权重）和 `equal_weight_index.py`（真实逐 bar 1/N 再平衡权重），adapter 从未提取——这是又一个"计算了但丢弃"的 Q4 缺口，效力标记 MEDIUM。

**prediction_arena（forecasting-tools + Kalshi）**——`report.prediction` 是真实模型输出的二元概率，`Q2` vs `Q3` 归属存在合理的双重解读（belief state vs predictive signal），审计明确标注为待人工裁决的歧义，未擅自二选一。

**vibe_trading（Vibe-Trading）**——本批"信息丢弃"最严重的案例：真实逐日 `positions.csv` 完整轨迹、真实 `TradeRecord` 订单历史、真实 LLM 生成并经过验证器循环校验的策略源码，adapter 目前只读取轨迹的最后一行，其余全部丢弃。其固定规则+LLM生成后即冻结的日频再平衡策略，也不能干净地套入现有任何一个 `PolicyType` 枚举值——已如实标记为 schema-fit 缺口，未强行归类。

---

## 五、项目—Q1/Q2/Q3/Q4 覆盖矩阵

`NATIVE` = 该 Q 层至少一个核心字段原生存在；`DERIVED`/`PARTIAL` = 需推导或仅部分能力；`UNSUPPORTED` = 该 Q 层完全不适用。

| Project | Q1 | Q2 | Q3 | Q4 |
|---|:-:|:-:|:-:|:-:|
| TradingAgents | NATIVE | NATIVE | UNSUPPORTED | UNSUPPORTED |
| ai-hedge-fund | NATIVE | PARTIAL(需启用更多 agent) | PARTIAL(personas+PEAD) | PARTIAL(需新代码) |
| FinGPT | UNSUPPORTED | NATIVE(窄) | UNSUPPORTED | UNSUPPORTED |
| Qlib | DERIVED | UNSUPPORTED | NATIVE | UNSUPPORTED(真实能力未接入) |
| RD-Agent | DERIVED(弱) | UNSUPPORTED | NATIVE | UNSUPPORTED |
| AlphaGen | DERIVED(弱) | UNSUPPORTED | NATIVE | UNSUPPORTED |
| FinRL | DERIVED(弱) | UNSUPPORTED | UNSUPPORTED | NATIVE |
| FinRL-Trading | DERIVED(弱) | NATIVE(需拆分自 Q4) | NATIVE | NATIVE |
| FinBERT | UNSUPPORTED | NATIVE | UNSUPPORTED | UNSUPPORTED |
| FinRobot | PARTIAL(需adapter注册工具) | PARTIAL | PARTIAL(弱) | PARTIAL(仅artifact) |
| FinMem | NATIVE | UNSUPPORTED | UNSUPPORTED | NATIVE(无权重) |
| FinAgent | NATIVE | PARTIAL(仅文本) | UNSUPPORTED | NATIVE(含权重) |
| AlphaForge | PARTIAL(非原生) | UNSUPPORTED | NATIVE | UNSUPPORTED |
| Alpha-GFN | UNSUPPORTED | UNSUPPORTED | PARTIAL(弱/demo) | UNSUPPORTED |
| TradeMaster | PARTIAL(独立pipeline) | UNSUPPORTED | PARTIAL(需monkey-patch) | NATIVE |
| skfolio | UNSUPPORTED | UNSUPPORTED | PARTIAL(弱) | NATIVE(条件性) |
| EarnMore | PARTIAL(非原生) | UNSUPPORTED | PARTIAL | NATIVE |
| PGPortfolio | PARTIAL(非原生) | UNSUPPORTED | UNSUPPORTED(内部未暴露) | NATIVE |
| DeepDow | PARTIAL(非原生) | PARTIAL(架构依赖) | PARTIAL(架构依赖) | NATIVE |
| Universal Portfolios | UNSUPPORTED | UNSUPPORTED | PARTIAL(勉强) | NATIVE |
| atlas | UNSUPPORTED | UNSUPPORTED | NATIVE | UNSUPPORTED |
| nofx | UNSUPPORTED | NATIVE | UNSUPPORTED(被丢弃) | UNSUPPORTED |
| finclaw | UNSUPPORTED | UNSUPPORTED | NATIVE | UNSUPPORTED(被丢弃) |
| deepalpha | NATIVE | UNSUPPORTED | NATIVE | UNSUPPORTED |
| agentictrading | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED | UNSUPPORTED(被丢弃) |
| prediction_arena | UNSUPPORTED | NATIVE | PARTIAL(与Q2重叠) | UNSUPPORTED |
| vibe_trading | UNSUPPORTED | UNSUPPORTED | PARTIAL | PARTIAL(被丢弃) |

---

## 六、原始功能与 Schema 对照 / 完整 CSV

逐字段级别的对照表（每行 = project × Q层 × canonical field，含 GitHub URL、commit hash、论文链接、映射状态、原始代码位置、转换方法、假设、信息损失、接入成本）见随附文件：

**`PROJECT_SCHEMA_AUDIT.csv`**（474 行数据，27 个项目，列：`project,github_url,commit_hash,paper_url,q_layer,canonical_field,mapping_status,native_path,transform,assumptions,loss_notes,adapter_effort`）

按项目分类汇总的"原始功能→当前输出"表格详见第四节各项目描述中引用的具体代码位置；完整逐字段表格因体量过大（474 行）不在本 Markdown 中重复，请查阅 CSV。

---

## 七、信息保留度与主要信息损失（汇总表）

| Project | Native Coverage | Recoverable Coverage | Information Retention | 主要信息损失 |
|---|---:|---:|---:|---|
| TradingAgents | 15-20% | 65-75% | ~70% | 风险三方辩论无专属字段；target_position 不可靠解析 |
| ai-hedge-fund | 20-25%(as-wrapped) | 65-70%(Q1/Q3) | ~45%(当前实现)/~70-75%(修复后) | **quantity 字段被现有代码丢弃**；persona 信号未启用 |
| FinGPT | 40-45% | 75-80% | ~90%(但能力面本身极窄) | 无 observation_window、无 confidence |
| Qlib | 35-40% | 75-80% | 85-90%（本批最高） | 158 因子只surface前5；无confidence |
| RD-Agent | 30% | 70-75% | 65-70% | 生成代码正文未持久化；迭代历史压缩 |
| AlphaGen | 35% | 75-80% | 75-80% | 因子池多表达式压缩成单字符串 |
| FinRL | 35-40% | 80% | 80-85% | checkpoint 未持久化；generation_window 架构缺口 |
| FinRL-Trading | 40% | 80-85% | 75-80% | **regime 探测器被错误路由到 Q4** |
| FinRobot | 分散(各Q<15%) | 分散 | ~50%（架构性缺口：最终分析只存在于聊天记录） | 唯一 NATIVE 是策略代码文件 artifact |
| FinMem | Q1 55-60%/Q4 35-40% | Q1 65-70% | ~95%（窄面高保真） | **Portfolio 无 cash 字段，target_weights 不可推导** |
| FinAgent | Q1 55-60%/Q4 40-45% | Q1 70-75% | 90-95%（三个LLM-agent中最高） | 无confidence；无bull/bear |
| AlphaForge | 10-15% | 45-50% | 55-60% | **GAN checkpoint 从不保存**；每日因子子集丢弃 |
| Alpha-GFN | 10% | 30-40% | ~80%（能力面极窄，demo级） | **无checkpoint保存/加载**；仅演示用途 |
| TradeMaster | 15% | 55-60% | 60-65% | DeepTrader打分张量被丢弃；约束因算法而异 |
| skfolio | 20% | 65-70% | 75-80%(需adapter自建WalkForward循环，否则~40%) | 无订单概念，只有连续权重 |
| EarnMore | 40-45% | 55-60% | ~85% | 无置信度；无解释文本 |
| PGPortfolio | 45-55% | 65-70% | 90-95%（本批最高） | 内部voting张量未暴露(需改上游代码) |
| DeepDow | 10-15% | 35-40% | 75-80%（能力面窄） | 架构依赖，多数网络无Q2/Q3产出 |
| Universal Portfolios | 20-25% | 45-50% | ~90% | BCRP/BestMarkowitz需明确排除避免违反因果性 |
| atlas | 高(Q3专注) | 高 | 高 | 已在生产环境接入，损失小 |
| nofx | 高(Q2专注) | 中 | 中 | **真实技术因子字典被丢弃**，未作为Q3输出 |
| finclaw | 高(Q3专注) | 中 | 中 | **74字段StrategyDNA完整策略基因组被丢弃**，未作为Q4输出 |
| deepalpha | 高 | 高 | 高 | 已在生产环境接入，损失小 |
| agentictrading | 极低(当前仅Q5) | 中(若重新提取) | 极低(当前) | **真实mean-variance/equal-weight权重从未提取** |
| prediction_arena | 高(Q2) | 中 | 高 | Q2/Q3归属歧义待人工裁决 |
| vibe_trading | 中 | 高(若重新提取) | 低(当前) | **完整逐日轨迹+订单历史仅读取末行** |

**Raw Archival Preservation**：27 个项目中绝大多数为 **Yes**（原始输出可完整归档进 `native_output`），FinRobot 为 **Partial**（聊天记录需要额外 hook 才能捕获）。

---

## 八、Adapter 接入优先级

### P0（最高优先级——已验证核心能力干净、成本可控，或修复成本极低价值极高）
- **ai-hedge-fund**：修复 `quantity` 字段丢弃 bug（LOW effort，立即见效）
- **FinRL**：Q4 权重+约束高保真原生，仅需解决 generation_window 架构问题（MEDIUM effort）
- **FinRL-Trading**：本批 Q3+Q4 最丰富，需同时修正 regime 字段错配（MEDIUM-HIGH effort）
- **Qlib**：Q3 信息保留度最高，MIT-兼容、无 API key、无 GPU（LOW effort）
- **FinMem**：Q1 干净原生 + 真实 checkpoint（LOW-MEDIUM effort）
- **FinAgent**：三个 LLM-agent 中 Q4 权重推导能力最强（LOW-MEDIUM effort）

### P1（值得接入，但成本或范围略逊于 P0）
- TradingAgents、RD-Agent、AlphaGen、FinBERT、FinRobot、TradeMaster、skfolio、EarnMore、PGPortfolio、Universal Portfolios
- ai-hedge-fund 的 Q3/Q4 扩展部分（区别于上面 P0 的字段修复）

### P2（有真实能力但成本高/范围窄/依赖重）
- DeepDow（架构依赖强）、AlphaForge（GPU+Qlib+BaoStock 全套依赖，无checkpoint）、Alpha-GFN（demo级，无checkpoint）、FinGPT（GPU 依赖重但产出极窄）、Qlib 的 Q4 扩展（真实但目前完全未用）

### 本地 7 个 adapter（已生产接入，优先级为"信息补全"而非"新接入"）
- **finclaw（P1 建议补全）**：提取 74 字段 StrategyDNA 作为 Q4 policy artifact
- **vibe_trading（P1 建议补全）**：提取完整 positions.csv 轨迹与订单历史作为 Q4 decisions
- **agentictrading（P1 建议补全，需先解决 Q5→Q4 重定位）**：提取真实 mean-variance/equal-weight 权重
- **nofx（P2 建议补全）**：暴露被丢弃的技术因子字典作为独立 Q3 信号
- atlas、deepalpha、prediction_arena：当前接入已较完整，无需大改

---

## 九、Schema 候选新增字段

三个候选，均满足"至少两个独立项目原生提供"标准，但**均未通过"必须加入"的三项门槛**（无一违反时间因果/执行完整性；现有字段虽有损但仍可表达），因此建议列为 `OPTIONAL_EXTENSION` 供未来评估，而非本次立即加入 CORE。

| 候选字段 | 所属Q | 支持项目 | 原始输出证据 | 当前字段为何无法表达 | 建议类型 | 预计覆盖提升 | 风险 | 结论 |
|---|---|---|---|---|---:|---|---|---|
| `iteration_history`（结构化多轮搜索/迭代历史） | Q3 | RD-Agent（`Trace.hist`，真实的假设-反馈迭代对）、AlphaGen（`pool.eval_cnt` 隐含的采样历史） | `Trace.hist` 真实存在并被下一轮 prompt 消费；AlphaGen 训练循环产生数百个候选表达式 | `EvidenceItem`/`explanation` 只能承载扁平化单次文本摘要，无法表达"提出→评估→修订"的有序链条 | OPTIONAL_EXTENSION | Q3 多轮搜索类项目 +10-15% 信息保留度 | 低——纯增量字段，不影响现有校验器 | 建议未来评估，本次不强制加入 |
| `sub_opinions: List[{source,view,confidence,reasoning}]`（N方独立子意见记录） | Q1 | TradingAgents（风险三方辩论）、ai-hedge-fund（13个persona + technicals/sentiment等 agent，均产出独立 `{signal,confidence,reasoning}`） | `risk_mgmt/{aggressive,conservative,neutral}_debator.py` 真实文本；`warren_buffett.py` 等13个persona文件均返回结构化signal | `bull_case`/`bear_case` 只适配二元辩论；`EvidenceItem` 无独立数值confidence槽位 | OPTIONAL_EXTENSION | Q1 多方聚合类项目 +10-15% 覆盖率 | 低——增量、可选 | 建议未来评估 |
| `EvidenceItem.relevance_score: Optional[float]`（检索相关性/显著性评分，非决策置信度） | Q1/Q2 | FinMem（`importance_score.py`/`recency.py`/`decay.py`/`compound_score.py` 真实排序分）、FinAgent（`DiverseQuery` embedding相似度排序） | 两个项目均真实计算并用于筛选top-k记忆，但排序分本身从未随证据一起保留 | `EvidenceItem` 目前无任何数值字段承载"为什么这条证据被选中"的排序依据 | OPTIONAL_EXTENSION | 两个记忆检索类项目 +5-10% 信息保留度 | 低 | 建议未来评估 |

未通过门槛、不予提出的相关想法（记录供参考）：AlphaForge 的"多因子集成权重"结构与 TradeMaster DeepTrader 的"被丢弃中间打分张量"存在表面相似性，但审计判断这不足以构成一个通用的"component contributions"字段提案——两者性质不同，且各自都只出现在单一项目中，不满足"至少两个独立项目"的门槛。

---

## 十、不建议加入 Schema 的项目特有能力

**全批统一排除（用户已明确指示，且每组调查均独立确认适用）**：Sharpe、total return、max drawdown、calibration error、adapter reliability、contradiction flag、fusion weight、benchmark comparison——凡属于回测/评价层的指标，无论多少项目原生产出，均不计入、不提议加入 adapter contract。这包括：agentictrading 的 mean-variance/equal-weight 回测曲线、FinRL/FinRL-Trading 的 Sharpe 打印、TradeMaster 的 test_result.csv 绩效、skfolio 的 problem_values_ 风险指标、vibe_trading/finclaw 的 walk-forward 回测统计、FinRobot 的 BackTrader Sharpe/Drawdown/TradeAnalyzer、AlphaGen/RD-Agent 的历史 IC 相关性诊断。

**项目特有实现细节，不建议泛化为 schema 字段**：
- AlphaForge 的"逐日因子池权重"多因子集成结构（仅此一个项目具备完整形态）
- TradeMaster DeepTrader 的丢弃中间打分张量（需 monkey-patch 才可获取，实现细节而非通用能力）
- Qlib 的 158 命名因子完整清单（`factor_expression` 已足够承载 top-N 代表性因子，无需扩展为因子清单字段）
- PGPortfolio 内部 `self.voting` 张量（需修改上游代码才能暴露，不符合薄封装原则，正确做法是保持 MISSING 而非新增字段强行迁就）
- finclaw 74 字段 `StrategyDNA` 的全部字段（`PolicyArtifact` 已足以承载整个基因组作为一个引用/序列化对象，无需逐字段拆解进 schema）

---

## 十一、证据不足和待人工确认事项

按重要性汇总（完整清单见各批次原始报告）：

1. **FinAgent 的论文归属是概率性推断，非确证**——仓库本身无论文链接、GitHub API description 为空，归属判断依据是术语匹配（`DiverseQuery`、"market intelligence"）与作者关联仓库网络（`FinAgentLight`/`FinWorld`/`EarnMore`），建议人工核实。
2. **TradeMaster 的官方实现判定**依据 README 自述与作者/机构匹配，OpenReview 论坛页面返回了反爬虫验证页无法直接读取，未独立核实论文 PDF 自身的代码可用性声明。
3. **AlphaForge 的官方实现判定**同样依据仓库自身 GitHub description 自称，未独立打开 AAAI/arXiv PDF 核实其 code-availability 语句；仓库无 LICENSE 文件，合规复用状态未定。
4. **ai-hedge-fund 缺少 DECISIONS.md 原始选型记录**——与其他项目不同，该 adapter 似乎早于决策日志规范建立，建议补做一次选型/安全审查记录。
5. **`adapters/vendor/*` 均为浅克隆（depth 1）**，已核实这些 vendor 目录当前 HEAD 与各现有 v1 adapter 文档中记录的原始 commit 均不一致（如 TradingAgents 记录的 `d751630` 在当前浅克隆中不可解析）——所有本次审计结论均基于**当前** HEAD，而非各 adapter 最初开发时的版本；升级/迁移前建议先确认这一时间差是否引入了破坏性上游变更。
6. **FinAgent 的 `look_forward_days` 窗口是否存在信息泄漏**未做端到端数据流全链路追踪，仅确认状态构造窗口本身不直接泄漏；建议人工做更彻底的因果性复核。
7. **prediction_arena 的 Q2 vs Q3 归属歧义**（`report.prediction` 既可视为信念状态也可视为预测信号）留待人工根据下游消费方式裁决，本次审计未擅自二选一。
8. **AlphaGen 的组织迁移历史**（`RL-MLDM/alphagen` → `ICT-FinD-Lab/alphagen`）仅通过当前 remote 配置与既有文档确认，未现场重新查询 GitHub API 的跳转链。
9. 所有 27 个项目均未实际执行训练/推理运行（遵守"不进行长时间训练、不下载大型数据集、不调用付费 API"的指示）——所有结论均来自静态代码阅读，未做端到端运行验证；这对 Alpha-GFN、AlphaForge 等依赖 GPU 训练的项目尤其重要，其真实产出数值特征未经实测确认。
10. Qlib 的 `qlib/contrib/strategy/`+`qlib/backtest/` Q4 扩展能力真实存在但未运行验证，作为 P2 提议前建议先端到端跑通一次确认无隐藏依赖问题（如是否需要实盘凭证等）。

---

*本报告及配套 CSV 系investigation-only产物，未修改 `CONTRACT/schemas.py`、任何 adapter 文件，或本仓库内任何生产代码。*
