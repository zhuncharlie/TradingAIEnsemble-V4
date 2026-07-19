"""
tests/test_harness_resume.py — resumability + atomic-write guarantees of
tools/run_large_scale_experiment.py (§八 of the Q4 stepwise infrastructure
task).

No conda subprocess dependency: tasks use `cmd=["python", "-c", ...]` against
whatever Python this test itself runs under (stdlib only), matching this
repo's "stdlib+pydantic only" test convention for harness-layer tests.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Loaded by explicit file path, not `import tools...`: some adapters (e.g.
# finagent_adapter.py) insert their own vendor dir at sys.path[0], and that
# vendor dir happens to contain its own unrelated `tools/` package, which can
# shadow this repo's real tools/ package as a namespace-package collision
# when the full test suite is discovered together. Loading by path sidesteps
# that entirely.
_spec = importlib.util.spec_from_file_location(
    "run_large_scale_experiment", ROOT / "tools" / "run_large_scale_experiment.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

atomic_write_json = _mod.atomic_write_json
is_already_done = _mod.is_already_done
result_path_for = _mod.result_path_for
run_batch = _mod.run_batch
run_task_with_retry = _mod.run_task_with_retry

PY = sys.executable


def _ok_task(name: str) -> dict:
    return {"name": name, "env": "n/a", "cmd": [PY, "-c", "print('ok')"]}


def _fail_task(name: str) -> dict:
    return {"name": name, "env": "n/a", "cmd": [PY, "-c", "import sys; sys.exit(1)"]}


class TestAtomicWrite(unittest.TestCase):
    def test_no_partial_file_left_on_write(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.result.json"
            atomic_write_json(p, {"status": "PASSED"})
            self.assertTrue(p.exists())
            leftovers = list(Path(d).glob("*.tmp*"))
            self.assertEqual(leftovers, [])
            self.assertEqual(json.loads(p.read_text())["status"], "PASSED")

    def test_overwrite_replaces_content(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.result.json"
            atomic_write_json(p, {"status": "FAILED"})
            atomic_write_json(p, {"status": "PASSED"})
            self.assertEqual(json.loads(p.read_text())["status"], "PASSED")


class TestSkipOnAlreadyDone(unittest.TestCase):
    def test_passed_result_is_skipped_on_rerun(self):
        with tempfile.TemporaryDirectory() as d:
            out_dir = Path(d)
            task = _ok_task("adapterA")
            r1 = run_task_with_retry(task, out_dir, default_timeout=10, max_retries=0, force=False)
            self.assertEqual(r1["status"], "PASSED")

            r2 = run_task_with_retry(task, out_dir, default_timeout=10, max_retries=0, force=False)
            self.assertEqual(r2["status"], "SKIPPED")

    def test_force_reruns_despite_existing_pass(self):
        with tempfile.TemporaryDirectory() as d:
            out_dir = Path(d)
            task = _ok_task("adapterB")
            run_task_with_retry(task, out_dir, default_timeout=10, max_retries=0, force=False)
            r2 = run_task_with_retry(task, out_dir, default_timeout=10, max_retries=0, force=True)
            self.assertEqual(r2["status"], "PASSED")
            self.assertNotEqual(r2.get("skip_reason"), True)

    def test_failed_result_is_not_skipped_on_rerun(self):
        with tempfile.TemporaryDirectory() as d:
            out_dir = Path(d)
            task = _fail_task("adapterC")
            r1 = run_task_with_retry(task, out_dir, default_timeout=10, max_retries=0, force=False)
            self.assertEqual(r1["status"], "FAILED")
            self.assertFalse(is_already_done(out_dir, "adapterC"))
            r2 = run_task_with_retry(task, out_dir, default_timeout=10, max_retries=0, force=False)
            self.assertEqual(r2["status"], "FAILED")  # re-attempted, not skipped


class TestResumeAcrossBatch(unittest.TestCase):
    def test_interrupted_batch_resumes_only_missing_tasks(self):
        with tempfile.TemporaryDirectory() as d:
            out_dir = Path(d)
            tasks = [_ok_task("a1"), _ok_task("a2"), _ok_task("a3")]

            # Simulate a partial prior run: only a1 completed.
            run_task_with_retry(tasks[0], out_dir, default_timeout=10, max_retries=0, force=False)
            self.assertTrue(is_already_done(out_dir, "a1"))
            self.assertFalse(is_already_done(out_dir, "a2"))
            self.assertFalse(is_already_done(out_dir, "a3"))

            results = run_batch(tasks, out_dir, default_timeout=10, max_retries=0, force=False)
            statuses = {r["name"]: r["status"] for r in results}
            self.assertEqual(statuses["a1"], "SKIPPED")
            self.assertEqual(statuses["a2"], "PASSED")
            self.assertEqual(statuses["a3"], "PASSED")

    def test_no_result_loss_after_resume(self):
        with tempfile.TemporaryDirectory() as d:
            out_dir = Path(d)
            tasks = [_ok_task("b1"), _ok_task("b2")]
            run_batch(tasks[:1], out_dir, default_timeout=10, max_retries=0, force=False)
            run_batch(tasks, out_dir, default_timeout=10, max_retries=0, force=False)
            for name in ("b1", "b2"):
                p = result_path_for(out_dir, name)
                self.assertTrue(p.exists())
                self.assertIn(json.loads(p.read_text())["status"], ("PASSED", "SKIPPED"))


if __name__ == "__main__":
    unittest.main()
