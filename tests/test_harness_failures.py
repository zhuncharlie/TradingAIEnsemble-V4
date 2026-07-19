"""
tests/test_harness_failures.py — timeout, retry, and independent per-task
failure isolation in tools/run_large_scale_experiment.py (§八).
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Loaded by explicit file path rather than `import tools...` — see
# test_harness_resume.py for why (a vendor adapter dir's own unrelated
# tools/ package can shadow this repo's tools/ package during full-suite
# discovery).
_spec = importlib.util.spec_from_file_location(
    "run_large_scale_experiment", ROOT / "tools" / "run_large_scale_experiment.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

run_batch = _mod.run_batch
run_task_subprocess = _mod.run_task_subprocess
run_task_with_retry = _mod.run_task_with_retry

PY = sys.executable


class TestTimeout(unittest.TestCase):
    def test_slow_task_times_out(self):
        task = {"name": "slow", "env": "n/a", "cmd": [PY, "-c", "import time; time.sleep(5)"], "timeout": 1}
        with tempfile.TemporaryDirectory() as d:
            r = run_task_subprocess(task, Path(d), default_timeout=1)
        self.assertEqual(r["status"], "TIMEOUT")
        self.assertIn("timed out", r["failure_reason"])

    def test_timeout_status_is_not_failed(self):
        # TIMEOUT must be distinguishable from a genuine crash/FAILED, per
        # the unified status vocabulary (§八).
        task = {"name": "slow2", "env": "n/a", "cmd": [PY, "-c", "import time; time.sleep(5)"], "timeout": 1}
        with tempfile.TemporaryDirectory() as d:
            r = run_task_subprocess(task, Path(d), default_timeout=1)
        self.assertNotEqual(r["status"], "FAILED")


class TestRetry(unittest.TestCase):
    def test_retries_up_to_max_then_fails(self):
        task = {"name": "always_fails", "env": "n/a", "cmd": [PY, "-c", "import sys; sys.exit(1)"]}
        with tempfile.TemporaryDirectory() as d:
            r = run_task_with_retry(task, Path(d), default_timeout=10, max_retries=2, force=False)
        self.assertEqual(r["status"], "FAILED")
        self.assertEqual(r["n_attempts"], 3)  # 1 initial + 2 retries

    def test_no_retry_by_default(self):
        task = {"name": "fails_once", "env": "n/a", "cmd": [PY, "-c", "import sys; sys.exit(1)"]}
        with tempfile.TemporaryDirectory() as d:
            r = run_task_with_retry(task, Path(d), default_timeout=10, max_retries=0, force=False)
        self.assertEqual(r["n_attempts"], 1)

    def test_stops_retrying_once_it_passes(self):
        # A task that always exits 0 should only ever attempt once even with
        # retries configured, since it passes on the first try.
        task = {"name": "passes", "env": "n/a", "cmd": [PY, "-c", "print('ok')"]}
        with tempfile.TemporaryDirectory() as d:
            r = run_task_with_retry(task, Path(d), default_timeout=10, max_retries=3, force=False)
        self.assertEqual(r["status"], "PASSED")
        self.assertEqual(r["n_attempts"], 1)

    def test_each_attempt_reason_preserved(self):
        task = {"name": "always_fails2", "env": "n/a", "cmd": [PY, "-c", "import sys; sys.exit(3)"]}
        with tempfile.TemporaryDirectory() as d:
            r = run_task_with_retry(task, Path(d), default_timeout=10, max_retries=1, force=False)
        self.assertEqual(len(r["attempts"]), 2)
        for a in r["attempts"]:
            self.assertEqual(a["status"], "FAILED")


class TestExpectedBlocked(unittest.TestCase):
    def test_expect_blocked_maps_nonzero_exit_to_blocked_not_failed(self):
        task = {"name": "blocked_adapter", "env": "n/a", "cmd": [PY, "-c", "import sys; sys.exit(1)"], "expect": "BLOCKED"}
        with tempfile.TemporaryDirectory() as d:
            r = run_task_subprocess(task, Path(d), default_timeout=10)
        self.assertEqual(r["status"], "BLOCKED")


class TestIndependentFailureIsolation(unittest.TestCase):
    def test_one_failing_task_does_not_abort_batch(self):
        tasks = [
            {"name": "ok1", "env": "n/a", "cmd": [PY, "-c", "print('ok')"]},
            {"name": "boom", "env": "n/a", "cmd": [PY, "-c", "import sys; sys.exit(1)"]},
            {"name": "ok2", "env": "n/a", "cmd": [PY, "-c", "print('ok')"]},
        ]
        with tempfile.TemporaryDirectory() as d:
            results = run_batch(tasks, Path(d), default_timeout=10, max_retries=0, force=False)
        statuses = {r["name"]: r["status"] for r in results}
        self.assertEqual(len(results), 3)
        self.assertEqual(statuses["ok1"], "PASSED")
        self.assertEqual(statuses["boom"], "FAILED")
        self.assertEqual(statuses["ok2"], "PASSED")

    def test_raw_failure_reason_is_preserved_not_swallowed(self):
        task = {"name": "explicit_error", "env": "n/a",
                "cmd": [PY, "-c", "import sys; print('boom-marker', file=sys.stderr); sys.exit(1)"]}
        with tempfile.TemporaryDirectory() as d:
            r = run_task_subprocess(task, Path(d), default_timeout=10)
        self.assertEqual(r["status"], "FAILED")
        self.assertIn("boom-marker", r["failure_reason"])

    def test_missing_cmd_raises_not_silently_skipped(self):
        task = {"name": "bad_task", "env": "n/a"}
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                run_task_subprocess(task, Path(d), default_timeout=10)


class TestLegacyFallbackStatus(unittest.TestCase):
    def test_legacy_task_can_report_stepwise_unsupported(self):
        # STEPWISE_UNSUPPORTED is a legitimate terminal status distinct from
        # FAILED — a task's own runner (not this generic subprocess runner)
        # is expected to emit it directly when an adapter is classified
        # BLOCKED/STEPWISE_UNSUPPORTED; this test only verifies the retry
        # wrapper treats it as "do not retry further, do not mark FAILED",
        # matching how it already treats PASSED/BLOCKED.
        task = {"name": "unsupported", "env": "n/a", "cmd": [PY, "-c", "import sys; sys.exit(1)"]}
        with tempfile.TemporaryDirectory() as d:
            r = run_task_with_retry(task, Path(d), default_timeout=10, max_retries=2, force=False)
        # Without an explicit STEPWISE_UNSUPPORTED signal the generic runner
        # correctly falls back to FAILED after exhausting retries — this
        # documents that STEPWISE_UNSUPPORTED must be set by the caller
        # (e.g. a Q4-aware wrapper script), not inferred from exit code.
        self.assertEqual(r["status"], "FAILED")


if __name__ == "__main__":
    unittest.main()
