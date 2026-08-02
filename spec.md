# credsniff — Project Specification

> A fast, local, zero-cloud secret scanner. Catch leaked API keys, tokens, and
> passwords before they ever reach a commit — without sending a single byte of
> your code to anyone.

**Status:** Draft v1 · **Owner:** s3rv3rnet · **Type:** CLI tool + reusable library (Python 3.11+)

---

## 1. Problem

Developers accidentally commit secrets — AWS keys, GitHub tokens, Stripe keys,
database passwords — into source code all the time. Once a secret is pushed to a
remote (especially a public repo), it is effectively compromised: bots scrape
GitHub for leaked keys within *seconds*, and a leaked cloud key can cost thousands
of dollars in minutes.

Existing solutions have real friction:

- **Cloud services (e.g. GitGuardian)** work well but send your code (or its
  metadata) to a third-party server, require an account, and gate features behind
  paid tiers. Not everyone can or wants to upload their private code.
- **Some open-source scanners** exist but are often clunky, hard to extend, or
  produce noisy, ugly output.

## 2. Goal

Build a **single command** a developer can run — `credsniff .` — that scans a
codebase for likely secrets and reports them clearly, running **100% locally**
with **no account, no network, no data leaving the machine**. It should be
trivial to install (`pip install credsniff`), pleasant to look at, easy to extend
with custom rules, and installable as a **pre-commit hook** so it blocks leaks
automatically.

### Guiding principles

1. **Local-first & private** — the tool never makes a network call. This is the
   headline differentiator; guard it fiercely.
2. **Zero-config by default, extensible when needed** — works instantly out of
   the box, but power users can add their own rules.
3. **Low friction** — one command, fast, readable output, CI-friendly exit codes.
4. **Honest about limits** — a scanner produces *suspicions*, not certainties. We
   surface likely secrets and mask them; we never claim to catch everything.

## 3. Non-goals (explicitly out of scope for v1)

- **No cloud/SaaS component, ever.** Local only.
- **No automatic remediation** (we report; we do not rewrite git history or rotate keys).
- **No full git-history rewriting.** (Scanning history is a possible v2; rewriting it is not our job.)
- **Not a general SAST tool.** We look for *secrets*, not code vulnerabilities.
- **No ML/AI in v1.** Detection is regex + entropy heuristics. (Keeps it a clean Phase 1 project.)

## 4. Users & use cases

| User | Use case |
|---|---|
| A solo developer | Run `credsniff .` before pushing, to catch a stray API key. |
| A team | Install the pre-commit hook so no one *can* commit a secret. |
| A CI pipeline | Run `credsniff . --format json` and fail the build on any finding. |
| A security-conscious dev | Scan a repo they're about to open-source. |

## 5. Functional requirements

### 5.1 Scanning
- **FR-1** Recursively scan a directory (or a single file) given as an argument; default to the current directory.
- **FR-2** Skip noise directories by default: `.git`, `node_modules`, `.venv`/`venv`, `__pycache__`, `dist`, `build`, and other caches.
- **FR-3** Skip binary/undecodable files gracefully (never crash on them).
- **FR-4** Read files **line by line** so memory stays flat even on large files.
- **FR-5** Report, for each finding: file path, line number, the rule that matched, a **masked** preview of the secret, and severity.

### 5.2 Detection
- **FR-6 (regex detector)** Match known secret patterns: AWS access key, GitHub token (classic + fine-grained), Google API key, Slack token, Slack webhook, Stripe live key, private-key PEM headers, and a generic `api_key = "..."` assignment pattern.
- **FR-7 (entropy detector)** Flag high-entropy strings (Shannon entropy above a configurable threshold) that no known pattern caught — this catches unknown/custom secrets.
- **FR-8 (custom rules)** Let users load additional rules from a YAML file via `--rules myrules.yaml`.

### 5.3 Output & exit codes
- **FR-9** Default output: a clean, colored terminal report (via `rich`), sorted most-severe first, with a summary line.
- **FR-10** `--format json` emits machine-readable JSON (for CI). Secrets are masked in output.
- **FR-11 (CI-friendly exit codes)** Exit `0` when clean, exit `1` when any secret is found. This is what lets CI and the pre-commit hook fail the build.
- **FR-12** `--quiet` suppresses the banner/summary; `--no-entropy` disables the entropy detector.

### 5.4 Pre-commit integration
- **FR-13** Ship a `.pre-commit-hooks.yaml` so any repo can add credsniff to its pre-commit config and block secret-containing commits.

## 6. Non-functional requirements
- **NFR-1 Privacy:** zero network calls. (Testable: the tool imports no HTTP client.)
- **NFR-2 Speed:** scan a typical repo (a few thousand files) in a couple of seconds.
- **NFR-3 Safety:** never print a secret in full — always mask.
- **NFR-4 Quality:** fully type-hinted, passes `ruff` + `mypy --strict`, `pytest` coverage > 80%.
- **NFR-5 Portability:** pure Python, works on macOS / Linux / Windows, no OS-specific code.

## 7. Architecture

A small pipeline with a pluggable detection layer:

```
                    ┌─────────────────────────────────────┐
   credsniff .  ──> │  CLI (typer)   cli.py                │
                    │   parses args, wires everything up   │
                    └───────────────┬─────────────────────┘
                                    │
                    ┌───────────────▼─────────────────────┐
                    │  Scanner   scanner.py                │
                    │   walks files (generators),          │
                    │   reads line by line,                │
                    │   asks each Detector about each line │
                    └───────┬───────────────────┬─────────┘
                            │                   │
          ┌─────────────────▼──┐      ┌─────────▼──────────────┐
          │ RegexDetector      │      │ EntropyDetector        │
          │ (known patterns    │      │ (high-randomness       │
          │  from rule packs)  │      │  unknown secrets)      │
          └─────────┬──────────┘      └─────────┬──────────────┘
                    │      implement Detector    │
                    └──────────┬─────────────────┘
                               ▼
                    ┌──────────────────────┐        ┌──────────────────┐
                    │ Findings (dataclass) │  ───>  │ Report (rich/json)│
                    └──────────────────────┘        └──────────────────┘
```

The key design choice is the **`Detector` Protocol** (Python's version of a Java
interface). The scanner knows *nothing* about how detection works — it just hands
each line to every detector and collects `Finding`s. Adding a new detection
strategy (or letting a user write one) requires zero changes to the scanner. This
is composition over inheritance, and it's the part that shows real design maturity.

## 8. Module breakdown

| Module | Responsibility | Key Python concept it teaches |
|---|---|---|
| `models.py` | `Severity` enum, `Rule`, `Finding`, `ScanResult` data classes | `dataclass`, `Enum` (≈ Java records/enums) |
| `utils.py` | Shannon entropy, secret masking, a `timed` decorator | decorators, functions |
| `detectors/base.py` | the `Detector` `Protocol` | interfaces / duck typing |
| `detectors/regex.py` | pattern-matching detector | regex, iterators |
| `detectors/entropy.py` | entropy-heuristic detector | generators, math |
| `rules.py` | built-in rule pack + YAML loader | data modeling, file I/O |
| `scanner.py` | file walking + orchestration | generators, `pathlib`, context managers |
| `report.py` | terminal + JSON output | `rich`, formatting |
| `cli.py` | the `credsniff` command | `typer`, exit codes |

## 9. CLI interface (contract)

```
credsniff [PATH]                 # scan PATH (default: current directory)

Options:
  --format [text|json]           # output format (default: text)
  --rules PATH                   # load extra rules from a YAML file
  --min-entropy FLOAT            # entropy threshold (default: 4.3)
  --no-entropy                   # disable the entropy detector
  --quiet                        # only print findings, no banner/summary
  --version                      # print version and exit

Exit codes:
  0  no secrets found
  1  one or more secrets found        <-- lets CI / pre-commit fail the build
  2  usage error (bad path, bad rules file)
```

## 10. Detection rules (initial built-in pack)

| Rule ID | What it catches | Example pattern (simplified) | Severity |
|---|---|---|---|
| `aws-access-key-id` | AWS access key | `AKIA[0-9A-Z]{16}` | high |
| `github-pat` | GitHub personal token | `ghp_[0-9A-Za-z]{36}` | high |
| `github-fine-grained` | GitHub fine-grained token | `github_pat_[0-9A-Za-z_]{82}` | high |
| `google-api-key` | Google API key | `AIza[0-9A-Za-z\-_]{35}` | high |
| `slack-token` | Slack token | `xox[baprs]-...` | high |
| `slack-webhook` | Slack webhook URL | `https://hooks.slack.com/services/...` | medium |
| `stripe-secret-key` | Stripe live secret key | `sk_live_[0-9A-Za-z]{24,}` | critical |
| `private-key` | PEM private key header | `-----BEGIN ... PRIVATE KEY-----` | critical |
| `generic-secret` | `api_key = "..."` assignments | `(?i)(api_key|secret|token|password)\s*[:=]\s*['"]...['"]` | medium |
| *(entropy)* | unknown high-randomness strings | Shannon entropy > threshold | low |

Custom rule pack YAML shape:

```yaml
rules:
  - id: acme-internal-token
    name: Acme internal token
    pattern: "acme_[0-9a-f]{32}"
    severity: high
    description: "Internal Acme service token"
```

## 11. Testing strategy
- **Unit:** entropy math (known inputs → known scores), masking, each rule against
  positive and negative sample strings, the YAML rule loader.
- **Integration:** scan a `tests/fixtures/` folder containing planted fake secrets
  and assert the exact findings; assert a clean folder yields zero findings and
  exit code 0.
- **CI:** GitHub Actions runs `ruff`, `mypy --strict`, and `pytest` on every push.

## 12. Milestones

- **M1 — Core scan works:** models + regex detector + scanner + basic text report; `credsniff .` finds a planted AWS key. *(MVP)*
- **M2 — Entropy + custom rules:** entropy detector and `--rules` YAML loading.
- **M3 — Polish:** `rich` report, JSON output, exit codes, `--` flags.
- **M4 — Distribution:** tests + CI green, pre-commit hook, README with demo GIF.
- **M5 — Ship:** publish to PyPI, tag `v0.1.0`, push to GitHub.

## 13. Future ideas (v2+, not now)
- Scan git *history* (past commits), not just the working tree.
- `--baseline` file to ignore known/accepted findings.
- Verify whether a found key is *live* (would require network — opt-in only, breaks the local-only promise, so gated behind an explicit flag).
- More rule packs contributed by the community.

---

*This spec is the north star for the build. If a decision during coding isn't
covered here, we update the spec first, then write the code — never the reverse.*
