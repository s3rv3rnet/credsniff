# Contributing to credsniff

Thanks for considering a contribution. This project has one hard promise —
**credsniff never sends your code anywhere** — and a lot of small rules that keep
it trustworthy. Both are described below.

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Ground rules

1. **No network calls, ever.** Not for telemetry, not for update checks, not for
   verifying whether a key is live. A PR that adds an HTTP client will be closed.
   This is the reason the project exists (see [spec.md](spec.md) §2).
2. **Never print a secret in full.** All output goes through masking.
3. **No real credentials anywhere** — not in tests, not in issues, not in commit
   messages. See [Test fixtures](#test-fixtures) below.

## Development setup

You need [uv](https://docs.astral.sh/uv/). Nothing else — not even a Python
install; uv fetches the interpreter.

```bash
git clone https://github.com/s3rv3rnet/credsniff
cd credsniff
uv sync                  # creates .venv and installs everything from uv.lock
uv run credsniff --help  # verify
```

There is no `activate` step. Prefix commands with `uv run` and the right
environment is used automatically.

### The checks that must pass

```bash
uv run ruff check .          # lint
uv run ruff format .         # format (--check in CI)
uv run mypy                  # type check, strict mode
uv run pytest                # tests
```

CI runs all four on Linux, macOS, and Windows across Python 3.11–3.13. Run them
locally first; it's much faster than waiting on CI.

Install the pre-commit hooks so this happens automatically:

```bash
uv run pre-commit install
```

### Dependencies

Use `uv add <pkg>` / `uv add --dev <pkg>` — never hand-edit `pyproject.toml`
dependency lists, and always commit the resulting `uv.lock`.

**New runtime dependencies are a big deal.** Every one enlarges the attack surface
of a security tool that people run on machines holding real credentials. Expect to
justify it; expect the answer to sometimes be "write the 30 lines instead".

## Adding a detection rule

Rules live in `src/credsniff/rules.py`. A good rule PR contains:

- the rule itself (`id`, `name`, `pattern`, `severity`, `description`)
- **positive samples** — strings that must match
- **negative samples** — near-miss strings that must *not* match, which is what
  keeps false positives down
- a note on where the pattern is documented, if the vendor publishes a format

### Regex requirements

Patterns run against arbitrary attacker-influenced file content, so:

- **No nested quantifiers** (`(a+)+`, `(\w*)*`). These cause catastrophic
  backtracking and can hang a scan — a denial of service in anyone's CI.
- **Bound your repetitions.** `{20,64}`, not `+`.
- Anchor with a distinctive prefix where the format has one (`AKIA`, `ghp_`,
  `sk_live_`). Prefix-anchored patterns are both faster and far less noisy.

### Test fixtures

Fake secrets in tests must be **structurally valid but provably dead**:

- prefer vendor-documented example values (e.g. AWS's `AKIAIOSFODNN7EXAMPLE`)
- generate throwaway PEM keys locally; never reuse one that touched a real system
- keep them under `tests/fixtures/`

This matters practically, not just in principle: a realistic-looking key in a
public repo gets scraped and tried within seconds, and GitHub push protection may
block your commit outright.

## Pull requests

- Branch from `main`.
- Keep PRs focused — one concern per PR.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `perf:`.
- **Sign off your commits** (`git commit -s`) to certify the
  [Developer Certificate of Origin](https://developercertificate.org/).
- Update `CHANGELOG.md` under `## [Unreleased]` in the same PR.
- New behaviour needs tests. Coverage must stay above 80%.

## Reporting bugs

Use the issue templates. For anything security-related, follow
[SECURITY.md](SECURITY.md) instead — do not open a public issue.

## Project layout

```
src/credsniff/
├── models.py       # Severity, Rule, Finding, ScanResult
├── utils.py        # entropy, masking
├── rules.py        # built-in rule pack + YAML loader
├── scanner.py      # file walking + orchestration
├── report.py       # terminal + JSON output
├── cli.py          # the credsniff command
└── detectors/
    ├── base.py     # the Detector protocol
    ├── regex.py
    └── entropy.py
```

Detectors are plugged in through a `Protocol` — the scanner knows nothing about how
detection works. To add a detection strategy, implement the protocol; you should not
need to modify `scanner.py`.
