# credsniff

**A fast, local, zero-cloud secret scanner.** Catch leaked API keys, tokens, and
passwords before they ever reach a commit — without sending a single byte of your
code to anyone.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Checked with mypy](https://img.shields.io/badge/mypy-strict-brightgreen.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/badge/linted%20with-ruff-261230.svg)](https://github.com/astral-sh/ruff)

> **Status: early development.** Not yet released to PyPI, and the commands below
> are not all implemented. See [Roadmap](#roadmap) for what works today.

---

## Why

A leaked cloud key is scraped from a public repo within *seconds* and can cost
thousands of dollars in minutes. The existing options each ask for something:
hosted scanners want your code on their servers and an account; other tools are
awkward to extend or noisy to read.

credsniff is one command, runs entirely on your machine, and needs no account.

**It never makes a network call.** Not for telemetry, not for update checks, not to
verify whether a key is live. That is the whole point of the project, and it is
enforced by a test in CI — not just a promise in a README.

## Install

```bash
uv tool install credsniff     # recommended
pipx install credsniff
pip install credsniff
```

Or run it without installing anything:

```bash
uvx credsniff .
```

## Usage

```bash
credsniff                     # scan the current directory
credsniff path/to/repo        # scan a specific path
credsniff . --format json     # machine-readable output, for CI
credsniff . --rules my.yaml   # add your own rules
```

### Options

| Flag | Description |
|---|---|
| `--format [text\|json]` | Output format (default: `text`) |
| `--rules PATH` | Load extra rules from a YAML file |
| `--min-entropy FLOAT` | Entropy threshold (default: `4.3`) |
| `--no-entropy` | Disable the entropy detector |
| `--quiet` | Only print findings — no banner or summary |
| `--version` | Print version and exit |

### Exit codes

| Code | Meaning |
|---|---|
| `0` | No secrets found |
| `1` | One or more secrets found |
| `2` | Usage error (bad path, bad rules file) |

Exit code `1` is what makes credsniff useful in CI and as a pre-commit hook: the
build fails when a secret shows up.

## What it detects

Built-in rules cover AWS access keys, GitHub tokens (classic and fine-grained),
Google API keys, Slack tokens and webhooks, Stripe live keys, PEM private-key
headers, and generic `api_key = "..."` assignments.

On top of that, an **entropy detector** flags high-randomness strings that no known
pattern matched — which is how unknown or custom secrets get caught.

### Custom rules

```yaml
rules:
  - id: acme-internal-token
    name: Acme internal token
    pattern: "acme_[0-9a-f]{32}"
    severity: high
    description: "Internal Acme service token"
```

```bash
credsniff . --rules acme-rules.yaml
```

## Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/s3rv3rnet/credsniff
    rev: v0.1.0
    hooks:
      - id: credsniff
```

## Limitations — please read

A secret scanner produces **suspicions, not proof**.

- **A clean scan is not a guarantee.** credsniff finds secrets matching known
  patterns or looking statistically random. A secret that resembles ordinary text
  will be missed. No scanner can promise otherwise; treat a clean result as one
  signal, not as clearance.
- **Expect false positives.** Test data, example keys, and hashes can trip the
  entropy detector. Tune with `--min-entropy`, or disable it with `--no-entropy`.
- **It scans your working tree, not your git history.** A secret already committed
  in an earlier commit will not be found. (History scanning is on the roadmap.)
- **We report; we do not remediate.** credsniff will not rewrite history or rotate
  keys. If it finds a real secret, **rotate the credential first** — removing it from
  the code is not enough once it has been pushed.

## Roadmap

- [x] Project scaffolding, tooling, CI
- [ ] **M1** — models, regex detector, scanner, text report
- [ ] **M2** — entropy detector, custom YAML rules
- [ ] **M3** — rich output, JSON format, exit codes, full CLI
- [ ] **M4** — test coverage, CI matrix, pre-commit hook
- [ ] **M5** — published to PyPI

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for setup and the
rules around adding detection patterns. Please read [SECURITY.md](SECURITY.md) before
reporting anything security-related, and note that **no real credentials belong in
issues, tests, or commits**.

## License

[MIT](LICENSE) © s3rv3rnet
