# Privacy policy

Usage Engineer (`ue`) runs entirely on your machine. It collects no data, has no telemetry,
no accounts, and no servers. `ue` itself opens no network connections.

## What it reads

- Codex session logs under `$CODEX_HOME` (default `~/.codex`) and the OpenCode database under
  `$XDG_DATA_HOME/opencode`, to count token usage. Only metadata such as token counts, timestamps
  and model names is reported; transcript text is not printed or stored.
- Files and command output you point it at (for example a log to compact or a project to map).
- `git` metadata of a project you pass to it.

## What it writes

Only to its state directory (`~/.usage-engineer`, or `UE_STATE_DIR`), and to profile files you
explicitly opt into with `apply-profile`, which can be undone with `rollback`. See the README for
the full list.

## Commands it runs for you

Some subcommands run a program you asked for: `git`, the command you wrap with the guard, or
`codex` during an opt-in `bench run --runner codex --confirm`. Those programs behave as they
normally do; for example Codex sends your prompts to OpenAI under OpenAI's own terms.

## Contact

Questions or concerns: open an issue at
https://github.com/noamshorts22-prog/usage-engineer/issues, or use "Report a vulnerability"
for anything sensitive (see [SECURITY.md](SECURITY.md)).
