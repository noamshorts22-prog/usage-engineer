# -*- coding: utf-8 -*-
"""Deterministic tests for ue.py - no network, no model calls, no user data touched.

Covers: stale context, retained error output, malformed logs, unknown metrics,
instruction preservation, apply/rollback conflict safety, compare comparability,
bench harness dry-run + fake-runner end-to-end.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="ue-selftest-"))
os.environ["UE_STATE_DIR"] = str(TMP / "state")
os.environ["CODEX_HOME"] = str(TMP / "codex-home")

TOOL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOL_DIR.parent))
from usage_engineer import ue  # noqa: E402


def run_cli(args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = ue.main(args)
    return code, buf.getvalue()


class TempDirMixin(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp(prefix="ue-case-"))

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)
        shutil.rmtree(TMP / "state", ignore_errors=True)


def write_rollout(root: Path, day: str, name: str, lines: list) -> Path:
    d = root / day.replace("-", "/")
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"rollout-{day}T00-00-00-{name}.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for obj in lines:
            f.write(json.dumps(obj) + "\n")
    return p


def token_event(inp, cached, out, reasoning, total):
    return {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": {
        "input_tokens": inp, "cached_input_tokens": cached, "cache_write_input_tokens": 0,
        "output_tokens": out, "reasoning_output_tokens": reasoning, "total_tokens": total}}}}


class TestAudit(TempDirMixin):
    def test_unknown_metrics_are_not_zero(self):
        root = self.work / "sessions"
        write_rollout(root, "2026-09-19", "a", [
            {"type": "event_msg", "payload": {"type": "task_started"}},
        ])
        rep = ue.audit_codex(root, since=None, max_files=None, max_file_mb=40)
        self.assertEqual(rep["sessions_without_usage"], 1)
        self.assertEqual(rep["sessions_with_usage"], 0)
        for k in ue._TOKEN_KEYS:
            self.assertIsNone(rep["usage_totals"][k], f"{k} must be UNKNOWN, not 0")
        self.assertIsNone(rep["requests_total"])

    def test_cumulative_usage_not_double_counted(self):
        root = self.work / "sessions"
        write_rollout(root, "2026-09-19", "b", [
            token_event(100, 40, 10, 5, 110),
            token_event(300, 120, 25, 8, 330),
        ])
        rep = ue.audit_codex(root, since=None, max_files=None, max_file_mb=40)
        self.assertEqual(rep["sessions_with_usage"], 1)
        self.assertEqual(rep["requests_total"], 2)
        self.assertEqual(rep["usage_totals"]["input_tokens"], 300)
        self.assertEqual(rep["usage_totals"]["cached_input_tokens"], 120)
        self.assertEqual(rep["usage_totals"]["output_tokens"], 25)

    def test_repeated_calls_detected(self):
        root = self.work / "sessions"
        call = {"type": "response_item", "payload": {"type": "custom_tool_call",
                "name": "shell", "input": {"command": "npm test"}}}
        write_rollout(root, "2026-09-19", "c", [call, call, call])
        rep = ue.audit_codex(root, since=None, max_files=None, max_file_mb=40)
        self.assertEqual(rep["sessions_with_repeated_calls"], 1)
        self.assertEqual(len(rep["top_repeated_calls"]), 1)
        self.assertEqual(list(rep["top_repeated_calls"].values())[0], 3)

    def test_oversized_output_bucket(self):
        root = self.work / "sessions"
        big = "x" * 60_000
        write_rollout(root, "2026-09-19", "d", [
            {"type": "response_item", "payload": {"type": "custom_tool_call_output", "output": big}},
        ])
        rep = ue.audit_codex(root, since=None, max_files=None, max_file_mb=40)
        self.assertEqual(rep["oversized_buckets"]["48000"], 1)
        self.assertGreaterEqual(rep["largest_output_chars"], 60_000)

    def test_malformed_lines_counted_not_crash(self):
        root = self.work / "sessions"
        d = root / "2026" / "09" / "19"
        d.mkdir(parents=True)
        (d / "rollout-2026-09-19T00-00-00-x.jsonl").write_text("{not json}\n", encoding="utf-8")
        rep = ue.audit_codex(root, since=None, max_files=None, max_file_mb=40)
        self.assertEqual(rep["files_total"], 1)
        self.assertEqual(rep["parse_errors_total"], 0)  # line not "interesting" => skipped
        rep2 = ue.parse_rollout_usage(d / "rollout-2026-09-19T00-00-00-x.jsonl")
        self.assertEqual(rep2["parse_errors"], 0)


class TestSummarizeLog(TempDirMixin):
    def test_failures_retained_and_full_copy_exact(self):
        log = self.work / "build.log"
        body = ["step 1 ok"] + [f"noise line {i}" for i in range(500)] + \
               ["error: cannot resolve module x", "step 3 ok", "FAILED test_foo"]
        body += [f"tail {i}" for i in range(30)]
        text = "\n".join(body)
        log.write_text(text, encoding="utf-8")
        # Treat the case dir as "home": temp is not under home on Linux/macOS runners.
        saved = ue.REDACTIONS
        ue.REDACTIONS = [(str(self.work), "%HOME%")]
        try:
            code, out = run_cli(["summarize-log", "--file", str(log), "--out", str(self.work / "s")])
        finally:
            ue.REDACTIONS = saved
        self.assertEqual(code, 0)
        summary = (self.work / "s" / "summary.md").read_text(encoding="utf-8")
        full = self.work / "s" / "full.log"
        self.assertTrue(full.exists())
        self.assertEqual(full.read_text(encoding="utf-8"), text)  # byte-faithful copy
        self.assertIn("error: cannot resolve module x", summary)
        self.assertIn("FAILED test_foo", summary)
        self.assertIn("full original:", summary)
        self.assertIn("%HOME%", summary)
        self.assertIn("full.log", summary)
        self.assertIn("omitted from THIS view", summary)

    def test_redact_covers_home_spellings(self):
        for variant, _ in ue.REDACTIONS:
            self.assertEqual(ue.redact(variant + os.sep + "x.log"), "%HOME%" + os.sep + "x.log")
        self.assertNotIn(ue.HOME_STR, ue.redact(ue.HOME_STR + os.sep + "a"))

    def test_malformed_binary_input(self):
        log = self.work / "blob.bin"
        data = b"\x00\x01\x02binary\x00junk"
        log.write_bytes(data)
        code, out = run_cli(["summarize-log", "--file", str(log), "--out", str(self.work / "s2")])
        self.assertEqual(code, 0)
        self.assertIn("binary", out.lower())
        self.assertEqual((self.work / "s2" / "full.log").read_bytes(), data)
        self.assertIn("UNKNOWN", out)

    def test_no_failures_does_not_claim_success(self):
        log = self.work / "quiet.log"
        log.write_text("\n".join(f"fine {i}" for i in range(50)), encoding="utf-8")
        code, out = run_cli(["summarize-log", "--file", str(log), "--out", str(self.work / "s3")])
        self.assertEqual(code, 0)
        self.assertIn("does not prove success", out)


class TestMap(TempDirMixin):
    def test_stale_detection_and_fresh(self):
        proj = self.work / "proj"
        (proj / "src").mkdir(parents=True)
        (proj / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        mapp = self.work / "map.json"
        code, _ = run_cli(["map", "build", "--project", str(proj), "--out", str(mapp)])
        self.assertEqual(code, 0)
        code, out = run_cli(["map", "check", "--project", str(proj), "--map", str(mapp)])
        self.assertEqual(code, 0)
        self.assertIn("FRESH", out)
        (proj / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
        code, out = run_cli(["map", "check", "--project", str(proj), "--map", str(mapp)])
        self.assertEqual(code, 1)
        self.assertIn("STALE", out)
        self.assertIn("src/a.py", out)

    def test_added_and_removed(self):
        proj = self.work / "proj2"
        proj.mkdir()
        (proj / "keep.txt").write_text("k", encoding="utf-8")
        (proj / "gone.txt").write_text("g", encoding="utf-8")
        mapp = self.work / "map2.json"
        run_cli(["map", "build", "--project", str(proj), "--out", str(mapp)])
        (proj / "gone.txt").unlink()
        (proj / "new.txt").write_text("n", encoding="utf-8")
        code, out = run_cli(["map", "check", "--project", str(proj), "--map", str(mapp)])
        self.assertEqual(code, 1)
        self.assertIn("new.txt", out)
        self.assertIn("gone.txt", out)


class TestInstructions(TempDirMixin):
    def test_duplicates_and_retained_mapping(self):
        f1 = self.work / "AGENTS.md"
        f2 = self.work / "other.md"
        shared = "Always run the project checks before claiming success."
        f1.write_text(shared + "\n\nUnique rule one.\n", encoding="utf-8")
        f2.write_text(shared + "\n\nUnique rule two.\n", encoding="utf-8")
        out = self.work / "dup.json"
        code, text = run_cli(["instructions", "duplicates", "--files", str(f1), str(f2),
                              "--json-out", str(out)])
        self.assertEqual(code, 0)
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(len(data["duplicate_groups"]), 1)
        self.assertEqual(data["duplicate_groups"][0]["count"], 2)
        mapped = {m["file"]: m["paragraph_hashes"] for m in data["retained_mapping"]}
        self.assertEqual(len(mapped), 2)
        shared_hash = ue.sha256_text(shared)
        self.assertIn(shared_hash, mapped[ue.redact(str(f1))])

    def test_verify_detects_missing_rule(self):
        f1 = self.work / "AGENTS.md"
        rule = "Never weaken tests to finish faster."
        f1.write_text(rule + "\n", encoding="utf-8")
        manifest_ok = self.work / "manifest_ok.json"
        manifest_ok.write_text(json.dumps([{"id": "no-weaken", "text": rule}]), encoding="utf-8")
        code, _ = run_cli(["instructions", "verify", "--files", str(f1),
                           "--manifest", str(manifest_ok)])
        self.assertEqual(code, 0)
        manifest_bad = self.work / "manifest_bad.json"
        manifest_bad.write_text(json.dumps([
            {"id": "no-weaken", "text": rule},
            {"id": "visual-check", "text": "Inspect rendered output at final quality."},
        ]), encoding="utf-8")
        code, out = run_cli(["instructions", "verify", "--files", str(f1),
                             "--manifest", str(manifest_bad)])
        self.assertEqual(code, 1)
        self.assertIn("visual-check", out)


class TestApplyRollback(TempDirMixin):
    def test_apply_then_clean_rollback(self):
        dest = ue.codex_home() / "usage-efficient.config.toml"
        code, _ = run_cli(["apply-profile", "--target", "codex"])
        self.assertEqual(code, 0)
        self.assertTrue(dest.exists())
        code, _ = run_cli(["rollback", "--target", "codex"])
        self.assertEqual(code, 0)
        self.assertFalse(dest.exists(), "rollback must remove a file that did not exist before")

    def test_rollback_aborts_on_later_edit(self):
        dest = ue.codex_home() / "usage-efficient.config.toml"
        run_cli(["apply-profile", "--target", "codex"])
        with open(dest, "a", encoding="utf-8") as f:
            f.write("# user edited this later\n")
        code, out = run_cli(["rollback", "--target", "codex"])
        self.assertEqual(code, 3)
        self.assertIn("CONFLICT", out)
        self.assertTrue(dest.exists())

    def test_opencode_project_aborts_on_existing_config(self):
        proj = self.work / "proj"
        proj.mkdir()
        (proj / "opencode.json").write_text("{}\n", encoding="utf-8")
        code, out = run_cli(["apply-profile", "--target", "opencode-project",
                             "--project", str(proj)])
        self.assertEqual(code, 3)
        self.assertIn("CONFLICT", out)

    def test_opencode_global_refused(self):
        code, out = run_cli(["apply-profile", "--target", "opencode-global"])
        self.assertEqual(code, 3)
        self.assertIn("REFUSED", out)


class TestCompare(TempDirMixin):
    def _rec(self, variant, cases):
        return {"variant": variant, "meta": {"model": "m"}, "cases": cases}

    def test_not_comparable_different_cases(self):
        a = self.work / "a.json"
        b = self.work / "b.json"
        a.write_text(json.dumps(self._rec("A", [
            {"id": "x", "accept_cmd": "c", "accept_pass": True, "usage": {"total": 10}}])),
            encoding="utf-8")
        b.write_text(json.dumps(self._rec("B", [
            {"id": "y", "accept_cmd": "c", "accept_pass": True, "usage": {"total": 10}}])),
            encoding="utf-8")
        code, out = run_cli(["compare", "--a", str(a), "--b", str(b)])
        self.assertEqual(code, 2)
        self.assertIn("NOT COMPARABLE", out)

    def test_quality_regression_flagged(self):
        a = self.work / "a.json"
        b = self.work / "b.json"
        ca = {"id": "x", "accept_cmd": "c", "accept_pass": True, "usage": {"total": 100}}
        cb = {"id": "x", "accept_cmd": "c", "accept_pass": False, "usage": {"total": 50}}
        a.write_text(json.dumps(self._rec("A", [ca])), encoding="utf-8")
        b.write_text(json.dumps(self._rec("B", [cb])), encoding="utf-8")
        code, out = run_cli(["compare", "--a", str(a), "--b", str(b)])
        self.assertEqual(code, 1)
        self.assertIn("QUALITY REGRESSION", out)
        self.assertIn("UNMEASURED", out)

    def test_both_pass_delta_reported(self):
        a = self.work / "a.json"
        b = self.work / "b.json"
        ca = {"id": "x", "accept_cmd": "c", "accept_pass": True,
              "usage": {"total": 100, "input": 80, "cached": 40, "output": 10,
                        "reasoning": 5, "requests": 2}}
        cb = dict(ca, usage={"total": 70, "input": 50, "cached": 30, "output": 8,
                             "reasoning": 4, "requests": 2})
        a.write_text(json.dumps(self._rec("A", [ca])), encoding="utf-8")
        b.write_text(json.dumps(self._rec("B", [cb])), encoding="utf-8")
        code, out = run_cli(["compare", "--a", str(a), "--b", str(b)])
        self.assertEqual(code, 0)
        self.assertIn("-30", out)
        self.assertIn("PRELIMINARY", out)


class TestContextPack(TempDirMixin):
    def test_pack_contains_identity_and_verification(self):
        proj = self.work / "proj"
        proj.mkdir()
        (proj / "app.py").write_text("print('hi')\n", encoding="utf-8")
        out = self.work / "pack.md"
        code, text = run_cli(["prepare-context", "--project", str(proj),
                              "--task", "Add a greeting flag.",
                              "--constraint", "No behavior change by default.",
                              "--verify", "python -m unittest",
                              "--relevant", "app.py", "--out", str(out)])
        self.assertEqual(code, 0)
        md = out.read_text(encoding="utf-8")
        self.assertIn("Add a greeting flag.", md)
        self.assertIn("No behavior change by default.", md)
        self.assertIn("python -m unittest", md)
        self.assertIn("app.py", md)
        self.assertIn("UNKNOWN", md)  # no git repo here
        self.assertIn("widen inspection", md)
        meta = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(meta["task_sha256"], ue.sha256_text("Add a greeting flag."))


class TestBench(TempDirMixin):
    def test_dry_run_refuses_over_cap(self):
        code, out = run_cli(["bench", "run-all", "--runner", "fake", "--max-calls", "2"])
        self.assertEqual(code, 2)
        self.assertIn("REFUSED", out)

    def test_dry_run_without_confirm_makes_no_calls(self):
        code, out = run_cli(["bench", "plan", "--case", "bugfix-offbyone"])
        self.assertEqual(code, 0)
        self.assertIn("planned model invocations: 2", out)
        self.assertIn("SPEND NOTE", out)

    def test_max_calls_required(self):
        code, out = run_cli(["bench", "run", "--case", "bugfix-offbyone", "--runner", "fake"])
        self.assertEqual(code, 2)
        self.assertIn("--max-calls is required", out)

    def test_fake_runner_end_to_end_all_cases(self):
        outdir = self.work / "runs"
        code, out = run_cli(["bench", "run-all", "--runner", "fake", "--max-calls", "8",
                             "--confirm", "--out", str(outdir)])
        self.assertEqual(code, 0, out[-2000:])
        summaries = list(outdir.glob("*summary.json"))
        self.assertEqual(len(summaries), 1)
        summary = json.loads(summaries[0].read_text(encoding="utf-8"))
        by_id = {}
        for c in summary["cases"]:
            by_id.setdefault(c["id"], []).append(c)
        self.assertEqual(len(by_id), 4)
        for cid, recs in by_id.items():
            for rec in recs:
                self.assertTrue(rec["accept_pass"], f"{cid}/{rec['variant']} should pass with solution")
        # solution/ and buggy/ must never be copied into an agent workdir
        for rec in summary["cases"]:
            wd = Path(rec["workdir"].replace("%HOME%", str(Path.home())))
            self.assertFalse((wd / "solution").exists())
            self.assertFalse((wd / "buggy").exists())


class TestRedaction(unittest.TestCase):
    def test_redact_home(self):
        s = str(Path.home() / "secret-project")
        self.assertNotIn(str(Path.home()), ue.redact(s))
        self.assertIn("%HOME%", ue.redact(s))


if __name__ == "__main__":
    unittest.main(verbosity=2)
