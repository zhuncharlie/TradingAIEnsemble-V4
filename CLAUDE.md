# CLAUDE.md — Global Instructions
# trading-ai-ensemble

## 1. Project Scope

This repository is a problem-driven research harness for integrating and
comparing heterogeneous open-source financial AI and quantitative trading
systems.

The current research framing uses four broad capability layers:

- Q1 — Action
- Q2 — State / Sentiment / Context
- Q3 — Signal / Alpha
- Q4 — Policy

These layers are research categories, not a permanently frozen list of fields,
methods, metrics, or policy types. The active contract version and the current
task define the exact implementation requirements.

Adapters must remain thin wrappers around real upstream projects. The upstream
project remains authoritative for its own models, trading logic, features,
optimization, and execution semantics.

---

## 2. Permanent Safety Rules

- Do not reimplement, replace, monkey-patch, or silently modify upstream
  trading logic.
- Do not fabricate unsupported fields, confidence values, explanations,
  evidence, horizons, labels, or outputs.
- Do not hardcode, print, log, serialize, or commit API keys or credentials.
- Do not create runtime dependencies between adapters.
- Do not make unrelated refactors or silently overwrite historical results.
- Modify only the files and direct dependencies required by the active task.
- Use offline, paper, simulation, or sandbox modes when practical.

A field may be populated only when it comes from:

- direct upstream output;
- a documented and reproducible derivation; or
- information explicitly supplied by the harness or task.

Otherwise, leave it unavailable according to the current contract.

---

## 3. Contract Protection

Files under `CONTRACT/` are protected shared interfaces.

Unless the active task explicitly authorizes a versioned contract migration:

- do not modify `CONTRACT/`;
- import the current contract instead of redefining it locally;
- report contract limitations rather than silently changing the interface.

During an explicitly authorized migration:

- modify only the named files and directly affected consumers;
- update the contract version;
- preserve semantic correctness over superficial backward compatibility;
- validate imports, construction, serialization, and relevant invalid cases;
- report affected consumers and unresolved compatibility issues;
- do not modify upstream trading logic.

After the authorized migration task ends, `CONTRACT/` returns to protected
status automatically.

---

## 4. Data, Provenance, and Causality

Keep the following artifacts separate:

1. native upstream output;
2. canonical adapter output;
3. mapped, normalized, corrected, or calibrated output;
4. fusion output;
5. execution and evaluation output.

Do not overwrite an earlier-stage artifact with a later-stage result.

Every derived result must remain traceable to its source inputs, transformation,
and material assumptions.

Preserve native output faithfully. If it is too large or not directly
serializable, preserve a faithful representation or artifact reference and
document any omitted content.

For Q4 and all time-dependent evaluation:

- future evaluation-period information must not influence earlier decisions;
- every decision must have a known or inferable information cutoff;
- trajectories must be generated causally, usually through stepwise execution.

Exact schema fields, provenance enums, calibration methods, fusion methods,
benchmarks, and metrics are defined by the active contract or experiment
specification, not by this file.

---

## 5. Validation and Completion

Run the tests and checks relevant to the active task.

Do not claim completion unless the relevant commands were actually executed.

Always report:

- commands run;
- passes, failures, and skipped checks;
- affected files or consumers;
- unresolved compatibility issues;
- known upstream, data, or reproducibility limitations.

Never delete tests, weaken validation, suppress failures, or fabricate passing
output merely to declare success.

The active task defines the authorized scope, but it never implicitly permits:

- rewriting upstream trading logic;
- fabricating information;
- exposing credentials;
- breaking provenance;
- violating time causality.
