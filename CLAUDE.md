# CLAUDE.md — Global Instructions for All Sessions
# trading-ai-ensemble

## Project Role

You are building ONE adapter for the trading-ai-ensemble framework.
This project aggregates multiple trading AI systems under a single interface,
so users can ask the same question (e.g. "Should I buy NVDA today?") and see
how different frameworks answer it — consensus vs. divergence, side by side.

Your job is narrow: wrap ONE upstream project. Do not touch anything else.

---

## Iron Rules (non-negotiable, applies to every session)

### 1. CONTRACT/ is read-only
Never modify any file inside `CONTRACT/`.
`CONTRACT/schemas.py`, `CONTRACT/base_adapter.py`, and `CONTRACT/test_harness.py`
are the shared contract between all adapters. Changing them breaks every other session.
If you think a schema field is missing, open a GitHub issue instead.

### 2. Wrap, never refactor
Do not modify the internal code of the upstream project you are integrating.
Your adapter is a **thin wrapper** — it calls the upstream API and translates
the output into the CONTRACT schema. That is all it does.

If you must patch the upstream project to make it work:
- Document the patch at the top of your adapter file with a `# PATCH:` comment
- Create `patches/{project_name}.diff` explaining why the patch is needed
- Never silently modify vendor code

### 3. One adapter, one file
Your entire adapter lives in `adapters/{your_adapter_name}_adapter.py`.
Do not create helper modules, shared utilities, or sub-packages.
The one exception: a `vendor/` subdirectory inside `adapters/` for git-cloned
upstream repos (add it to `.gitignore`).

### 4. Do not read or import other adapters
Never import from `adapters/finrl_adapter.py` or any other adapter.
Each adapter is independently runnable and independently testable.

### 5. Validate before you call it done
Run this command and paste the output into your response:
```
python CONTRACT/test_harness.py --adapter adapters/YOUR_ADAPTER_FILE.py
```
All checks must pass. A smoke test that prints "✓ 8/8 checks passed" is the
only acceptable definition of "done."

### 6. API keys via environment only
Never hardcode API keys. Always read from `os.environ["KEY_NAME"]`.
Never print or log key values.

---

## File Layout

```
trading-ai-ensemble/
├── CONTRACT/                    ← READ-ONLY. The shared contract.
│   ├── schemas.py               ← Pydantic models for Q1–Q5
│   ├── base_adapter.py          ← Abstract BaseAdapter class
│   └── test_harness.py          ← Validation runner
│
├── adapters/                    ← One file per upstream project
│   ├── example_stub_adapter.py  ← Reference implementation — read this first
│   └── YOUR_adapter.py          ← Your deliverable
│
├── results/                     ← Output JSONs (auto-created by adapters)
│   └── {task_id}/
│       └── {adapter_name}.json
│
└── patches/                     ← Only if upstream patching was unavoidable
    └── {project_name}.diff
```

---

## The Five Questions (Q-schema overview)

Each upstream project answers a subset of these. Your adapter only needs to
implement the methods for questions the upstream project actually answers.

| Q  | Question | Output schema | Key fields |
|----|----------|---------------|------------|
| Q1 | Should I buy / sell / hold this stock? | `Q1Decision` | action, confidence, reasoning |
| Q2 | What is the market sentiment / risk? | `Q2Sentiment` | sentiment_score (−1→+1), risk_level, drivers[] |
| Q3 | Are there unusual signals or alpha? | `Q3Signal` | signal_type, strength, supporting_evidence[] |
| Q4 | How should I allocate my portfolio? | `Q4Portfolio` | weights {ticker: float}, cash_ratio |
| Q5 | How has this strategy performed historically? | `Q5Backtest` | sharpe, max_drawdown, total_return |

All schemas are in `CONTRACT/schemas.py`. Import from there, never redefine.

---

## How to Start (read this before writing a single line of code)

1. Read `CONTRACT/base_adapter.py` — understand the interface you must implement
2. Read `CONTRACT/schemas.py` — understand the output types you must return
3. Read `adapters/example_stub_adapter.py` — see a complete minimal implementation
4. Read the upstream project's README (URL in your session brief)
5. Write `adapters/{name}_adapter.py` — subclass BaseAdapter, implement q*() methods
6. Run `python CONTRACT/test_harness.py --adapter adapters/{name}_adapter.py --smoke` (fast check)
7. Run `python CONTRACT/test_harness.py --adapter adapters/{name}_adapter.py` (full check)
8. Paste the output. All checks must be green.

---

## Minimum Viable Adapter Checklist

- [ ] `name` class attribute set (snake_case, unique)
- [ ] `questions_answered` class attribute set (e.g. `["Q1", "Q2"]`)
- [ ] `upstream_repo` class attribute set (GitHub URL)
- [ ] At least one q*() method implemented and returning a valid schema object
- [ ] `smoke_test()` overridden to call real upstream code (even with stubbed data)
- [ ] `python CONTRACT/test_harness.py --adapter adapters/YOUR_FILE.py` → all green
- [ ] Result written to `results/{task_id}/{adapter_name}.json`

---

## What "Encapsulation" Means Here

Good encapsulation (do this):
```python
# Call upstream API → translate output → return schema object
result = upstream_lib.analyze(ticker, date)
return Q1Decision(
    action=Action.BUY if result["signal"] > 0 else Action.SELL,
    confidence=result["confidence"],
    reasoning=result["rationale"],
    ...
)
```

Bad (never do this):
```python
# Modifying upstream internals
upstream_lib.internal_module.SomeClass._hidden_method = my_replacement

# Reimplementing upstream logic
def my_own_sentiment_scorer(text):   # ← this belongs in the upstream project
    ...
```

The rule: if a bug in your adapter means the upstream project's output is wrong,
fix the upstream project (via a patch file). If a bug means the translation to
our schema is wrong, fix the adapter. Never mix the two.

---

## Registered Adapters (do not duplicate)

| Adapter file | Project | Questions |
|---|---|---|
| `finrl_adapter.py` | AI4Finance/FinRL | Q4, Q5 |
| `tradingagents_adapter.py` | TauricResearch/TradingAgents | Q1, Q2 |

Check this table before starting. If your project is already listed, ask
the project maintainer before creating a second adapter for the same upstream.
