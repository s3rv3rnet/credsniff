# Security Policy

credsniff is a security tool. It reads every file in a repository, executes
pattern matching against untrusted content, and is designed to sit in the commit
path — so we take reports about it seriously.

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Use GitHub's [private vulnerability reporting][pvr] on this repository:
**Security → Report a vulnerability**. If that is unavailable to you, email
manikanta.maddali.coding@gmail.com.

[pvr]: https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability

Please include:

- the version (`credsniff --version`) and how you installed it
- a minimal reproducer
- what you expected versus what happened

**Never include a real secret in a report.** If a bug involves a specific
credential, redact it — `AKIA****************` is enough for us to work with. If
you believe a real credential of yours was exposed by a credsniff bug, rotate it
first, then report.

### What to expect

| | Target |
|---|---|
| Acknowledgement | within 3 days |
| Initial assessment | within 7 days |
| Fix or mitigation plan | within 30 days for confirmed issues |

We will credit you in the advisory and the changelog unless you prefer otherwise.
Coordinated disclosure: we ask for a reasonable window to ship a fix before public
details are published.

## Supported versions

While the project is pre-1.0, only the latest released version receives security
fixes.

| Version | Supported |
|---|---|
| latest `0.x` | ✅ |
| older `0.x` | ❌ |

## In scope

Reports we especially want:

- **Secret leakage by the tool itself** — any path where credsniff writes, logs, or
  displays an unmasked secret, including in error messages and tracebacks.
- **Any network activity.** credsniff makes no network calls, by design. A build or
  code path that contacts the network is a security bug, not a feature request.
- **Denial of service** — a repository or `--rules` file that makes credsniff hang or
  exhaust memory (for example, catastrophic regex backtracking).
- **Code execution** via a crafted rules file, scanned content, or configuration.
- **Path traversal** — the scanner reading files outside the directory it was given.
- **Supply chain** — problems with our published artifacts, release workflow, or
  dependency set.

## Out of scope

- **Missed secrets (false negatives).** credsniff produces *suspicions, not proof*.
  A clean scan is not a guarantee that a repository contains no secrets, and no
  scanner can offer one. Please report these as regular issues so we can improve the
  rules — they are bugs, just not security vulnerabilities.
- **False positives.** Also a regular issue.
- Vulnerabilities in a dependency that we do not expose, and that have no impact on
  credsniff's behaviour.

## Our own security practices

- No network calls, enforced by a test in CI.
- Secrets are masked at the point of construction, so an unmasked value is never
  held in a result object.
- Rules files are parsed with `yaml.safe_load` only.
- Dependencies are fully pinned in `uv.lock` and audited in CI.
- Releases are published to PyPI via trusted publishing (OIDC), with no long-lived
  API tokens.
