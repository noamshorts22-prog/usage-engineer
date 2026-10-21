# usage-engineer (`ue`)

[![CI](https://github.com/noamshorts22-prog/usage-engineer/actions/workflows/ci.yml/badge.svg)](https://github.com/noamshorts22-prog/usage-engineer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

**Stop paying for wasted agent work.** `ue` is a local CLI that measures and cuts the work coding
agents throw away: 5,000-line logs pasted into context, the same failing command retried, stale
project maps, duplicated instructions. It works with **Codex CLI** and **OpenCode**.

- Zero dependencies, one Python file, no network calls, ever.
- Never reads `auth.json`, cookies, tokens or chat text.
- Never changes your model or reasoning settings. Everything that writes is opt-in and reversible.

## Install

```
pipx install git+https://github.com/noamshorts22-prog/usage-engineer
ue doctor
```

Or run from a checkout with `python ue.py <command>` (Windows: `ue.cmd <command>`).

## Two minutes to your first numbers

```
ue audit                      # where did my Codex/OpenCode usage go? (read-only, redacted)
ue summarize-log --file build.log   # keep every error, drop the noise, store the full copy
ue map build --project .      # snapshot the project; `map check` tells you when it is stale
```

## Commands

| command | what it does | writes |
|---|---|---|
| `audit` | usage baseline from local Codex rollout JSONL and the OpenCode SQLite DB, with waste signals; redacted | optional JSON via `--json-out` |
| `summarize-log --file X` | compact view that keeps every failure/error line plus context; stores the byte-exact original and prints its path | `--out` dir |
| `prepare-context --project DIR` | small task pack: request, constraints, git commit/diff id, path hashes, verification commands | `--out` md + json |
| `map build` / `map check` | versioned project map; `check` exits 1 and lists files when anything changed | map json |
| `instructions scan/duplicates/verify` | AGENTS.md inventory, paragraph-level duplicate mapping, mandatory-rule verification | optional json |
| `compare --a R1 --b R2` | per-task paired comparison of two bench runs; refuses non-comparable records; flags quality regressions | stdout |
| `apply-profile --target codex` | opt-in Codex profile `$CODEX_HOME/usage-efficient.config.toml`, used via `codex --profile usage-efficient` | profile + backup + registry |
| `apply-profile --target opencode-project --project DIR` | project `opencode.json` that references the ue instructions (aborts if one exists) | project file |
| `rollback --target codex` | restores the original state; aborts if the file changed after apply | - |
| `bench list/plan` | the 4 frozen paired benchmark cases and the exact commands (no model calls) | stdout |
| `bench run --runner codex --max-calls N --confirm` | opt-in live A/B run with a hard invocation cap and no automatic retries | state dir |
| `doctor` | environment check: versions, config paths, profiles | stdout |
| `selftest` | 25 deterministic tests, no model calls | - |

## Measure before you believe

Efficiency claims about agents are cheap. `ue bench` makes them testable: each of the four frozen
cases (off-by-one bugfix, cross-file rename, regression test, RTL layout fix) runs in a fresh
isolated copy, the agent never sees the solution or the acceptance script, and `ue compare` refuses
to compare runs that used different models, reasoning levels or case versions.

```
ue bench plan
ue bench run-all --runner codex --max-calls 8 --confirm
ue compare --a <baseline-run.json> --b <profile-run.json>
```

## Safety properties

- Audit output never includes transcript text and redacts your home directory as `%HOME%`.
- Unknown metrics are reported as `UNKNOWN` / `null`, never as `0`.
- `apply-profile` backs up any existing file and records its SHA-256; `rollback` refuses to
  overwrite later edits (exit code 3).
- `apply-profile --target opencode-global` is refused by design.
- Benchmarks refuse to run without `--max-calls` and `--confirm`. `ue` caps the number of
  invocations; it cannot cap tokens or money.

State lives in `~/.usage-engineer` (override with `UE_STATE_DIR`).

## Known limitations

- Model-level efficiency is unmeasured until you run `bench` yourself, because live runs cost quota.
- Token figures derived from character counts are estimates (4 characters per token).
- The OpenCode audit covers `session` table totals, not per-message parsing.

## Roadmap

- Claude Code, Gemini CLI and Aider support in `audit` and `bench`
- A GitHub Action that posts `ue audit` waste signals on agent-authored PRs
- More benchmark cases, contributed by the community

Contributions welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
