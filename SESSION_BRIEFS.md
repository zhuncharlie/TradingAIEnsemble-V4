# Session Briefs — Copy-paste for each new Claude Code session

Each section below is a self-contained prompt for one Claude Code session.
Open a new terminal, `cd ~/projects/trading-ai-ensemble`, then paste the brief.

---

## Session A — ai-hedge-fund (Q1)

```
I'm building a multi-framework trading AI ensemble system called trading-ai-ensemble.
Your job: write ONE adapter that wraps the ai-hedge-fund project.

Working directory: ~/projects/trading-ai-ensemble

FIRST — read these files before writing any code:
1. CLAUDE.md                          (project rules — mandatory)
2. CONTRACT/base_adapter.py           (interface you must implement)
3. CONTRACT/schemas.py                (output types you must return)
4. adapters/example_stub_adapter.py   (reference implementation)

Upstream project:
  GitHub: https://github.com/virattt/ai-hedge-fund
  What it does: Multi-agent LLM system — bull analyst, bear analyst, risk manager,
                portfolio manager — debates whether to BUY/SELL/HOLD a stock.
  Questions answered: Q1 (buy/sell/hold decision)

Your deliverable:
  adapters/ai_hedge_fund_adapter.py

Rules (also in CLAUDE.md):
- Do NOT modify any file inside CONTRACT/
- Do NOT modify the upstream project's internal code
- Wrap it, don't refactor it
- Minimum viable version first: one ticker, one date, working smoke test
- If a separate conda env is needed, document it at the top of the file

Done = python CONTRACT/test_harness.py --adapter adapters/ai_hedge_fund_adapter.py
       prints "all checks passed". Paste that output when you're finished.
```

---

## Session B — FinGPT (Q2)

```
I'm building a multi-framework trading AI ensemble system called trading-ai-ensemble.
Your job: write ONE adapter that wraps FinGPT for sentiment scoring.

Working directory: ~/projects/trading-ai-ensemble

FIRST — read these files before writing any code:
1. CLAUDE.md                          (project rules — mandatory)
2. CONTRACT/base_adapter.py           (interface you must implement)
3. CONTRACT/schemas.py                (output types — focus on Q2Sentiment)
4. adapters/example_stub_adapter.py   (reference implementation)

Upstream project:
  GitHub: https://github.com/AI4Finance-Foundation/FinGPT
  What it does: Fine-tuned LLM that scores news/social media sentiment for stocks.
                Outputs a sentiment score (positive/negative/neutral) per article,
                then aggregates to a stock-level score.
  Questions answered: Q2 (market sentiment and risk level)

Target output: Q2Sentiment with:
  sentiment_score: float in [-1.0, +1.0]  (aggregate across news sources)
  risk_level: LOW / MEDIUM / HIGH / EXTREME
  drivers: list of top 3 contributing news headlines or factors

Your deliverable:
  adapters/fingpt_adapter.py

Rules:
- Do NOT modify CONTRACT/ files
- Do NOT modify FinGPT internals
- If FinGPT requires a HuggingFace model download, document in README comment
- Minimum viable: process 1 ticker, 1 date, return Q2Sentiment

Done = python CONTRACT/test_harness.py --adapter adapters/fingpt_adapter.py → all green
```

---

## Session C — DeepAlpha / ML ensemble (Q1)

```
I'm building a multi-framework trading AI ensemble system called trading-ai-ensemble.
Your job: write an adapter that wraps a gradient-boosted ML factor model for Q1 decisions.

Working directory: ~/projects/trading-ai-ensemble

FIRST — read these files before writing any code:
1. CLAUDE.md
2. CONTRACT/base_adapter.py
3. CONTRACT/schemas.py  (focus on Q1Decision)
4. adapters/example_stub_adapter.py

Upstream project:
  What it does: XGBoost + LightGBM + CatBoost ensemble on technical factors
                (RSI, MACD, Bollinger Bands, volume features). Outputs a
                probability that the stock outperforms the market next N days.
  Questions answered: Q1 (buy/sell/hold), Q3 (factor signal)

Note: If no public "DeepAlpha" repo exactly matches the image description,
find the closest open-source gradient-boosted trading model on GitHub.
Document your choice in the adapter file header. Prefer repos with:
  - XGBoost/LGB/CatBoost ensemble
  - technical factor features
  - forward return prediction

Your deliverable:
  adapters/deepalpha_adapter.py

Done = python CONTRACT/test_harness.py --adapter adapters/deepalpha_adapter.py → all green
```

---

## Session D — FinClaw (Q3)

```
I'm building a multi-framework trading AI ensemble system called trading-ai-ensemble.
Your job: wrap FinClaw for Q3 alpha signal detection.

Working directory: ~/projects/trading-ai-ensemble

FIRST — read: CLAUDE.md, CONTRACT/base_adapter.py, CONTRACT/schemas.py (Q3Signal),
        adapters/example_stub_adapter.py

Upstream project:
  GitHub: search GitHub for "FinClaw" or "484 alpha factors genetic algorithm trading"
  What it does: 484 alpha factors, genetically-evolved, with forward-validation.
                Selects the most predictive factors for a given stock/period.
  Questions answered: Q3 (alpha signal — which factors are firing right now)

Target output: Q3Signal with:
  signal_type: one of MOMENTUM / REVERSAL / BREAKOUT / ANOMALY / FACTOR
  direction: LONG / SHORT / NEUTRAL
  strength: 0.0–1.0 (factor z-score normalised)
  supporting_evidence: top 3 factor names with their values

Your deliverable: adapters/finclaw_adapter.py

Done = python CONTRACT/test_harness.py --adapter adapters/finclaw_adapter.py → all green
```

---

## Session E — Vibe-Trading (Q3 + Q4 + Q5)

```
I'm building a multi-framework trading AI ensemble system called trading-ai-ensemble.
Your job: wrap Vibe-Trading — it answers THREE questions (Q3, Q4, Q5).

Working directory: ~/projects/trading-ai-ensemble

FIRST — read: CLAUDE.md, CONTRACT/base_adapter.py, CONTRACT/schemas.py (Q3+Q4+Q5),
        adapters/example_stub_adapter.py

Upstream project:
  GitHub: search for "Vibe-Trading" — it's a natural-language strategy generation +
          multi-market backtesting system with a CompositeEngine for portfolio allocation.
  Questions answered: Q3 (natural-language alpha signal), Q4 (portfolio weights via
                      CompositeEngine), Q5 (backtest across 7 market types)

This adapter implements ALL THREE q methods: q3_signal(), q4_portfolio(), q5_backtest()
Set questions_answered = ["Q3", "Q4", "Q5"]

Start with the minimum: get Q5 (backtest) working first since it has the richest
historical data output. Then Q4, then Q3.

Your deliverable: adapters/vibe_trading_adapter.py

Done = python CONTRACT/test_harness.py --adapter adapters/vibe_trading_adapter.py → all green
```

---

## Session F — FinRL-X (Q3 + Q4)

```
I'm building a multi-framework trading AI ensemble system called trading-ai-ensemble.
Your job: wrap FinRL-X for Q3 (factor signal) and Q4 (adaptive portfolio allocation).

Working directory: ~/projects/trading-ai-ensemble

FIRST — read: CLAUDE.md, CONTRACT/base_adapter.py, CONTRACT/schemas.py (Q3+Q4),
        adapters/example_stub_adapter.py

Upstream project:
  GitHub: search for "FinRL-X" or "AI4Finance FinRL-X adaptive DRL"
  What it does: Adaptive DRL that switches between growth/defensive/neutral regimes.
                Selects top 25% NASDAQ stocks using ML factors, then allocates via DRL.
  Questions answered: Q3 (ML factor stock selection), Q4 (DRL portfolio allocation)

Note: FinRL (not FinRL-X) is already integrated — check adapters/finrl_adapter.py
      so you understand the precedent. FinRL-X is the adaptive/regime-switching variant.

Your deliverable: adapters/finrl_x_adapter.py

Done = python CONTRACT/test_harness.py --adapter adapters/finrl_x_adapter.py → all green
```
