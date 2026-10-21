# Contributing

Thanks for helping. `ue` is a single-file, zero-dependency Python CLI; keep it that way.

## Setup

```
git clone https://github.com/noamshorts22-prog/usage-engineer
cd usage-engineer
python ue.py selftest
```

## Rules every change must keep

1. **No network calls.** Not for telemetry, not for update checks.
2. **Never read credentials or chat text.** `auth.json`, cookies and tokens are off limits; audit output
   holds metadata only and redacts the home directory.
3. **Unknown is not zero.** A metric we cannot measure is `null` / `UNKNOWN`.
4. **Every write is reversible.** Anything that edits user config records a backup and a SHA-256 so
   `rollback` can refuse to clobber later edits.
5. **Tests are deterministic.** No model calls; use the `fake` runner.

Add a test in `usage_engineer/tests/test_ue.py` for every behaviour change.

## Good first contributions

- Support for another agent CLI (Claude Code, Gemini CLI, Aider) in `audit` and `bench`.
- New benchmark cases under `usage_engineer/benchmarks/fixtures/` with frozen acceptance checks.
- New waste signals in `audit` (for example repeated identical tool calls).
