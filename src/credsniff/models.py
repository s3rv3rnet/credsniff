"""Core data types shared by every part of credsniff."""

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final


class Severity(StrEnum):
    """How serious a finding is.

    Members are plain lowercase strings, so they serialise straight to JSON
    without a custom encoder (FR-10).

    Order severities with :attr:`rank`. Do not use ``<`` or ``>`` directly:
    ``StrEnum`` inherits those from ``str``, where they mean alphabetical
    comparison, not severity.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        """Numeric severity, where higher is more severe.

        Use as a sort key. Not meaningful for equality — compare members
        directly for that.
        """
        return _RANKS[self]


_RANKS: Final[dict[Severity, int]] = {
    Severity.CRITICAL: 4,
    Severity.HIGH: 3,
    Severity.MEDIUM: 2,
    Severity.LOW: 1,
}


@dataclass(frozen=True, slots=True)
class Rule:
    """A named pattern that identifies one kind of secret.

    Attributes:
        id: Stable identifier used in reports, e.g. ``aws-access-key-id``.
        name: Human-readable name shown to the user.
        pattern: Pre-compiled regex. Callers compile once at load time rather
            than per line, so scanning stays fast (NFR-2).
        severity: How serious a match is.
        description: Optional longer explanation of what the rule catches.
    """

    id: str
    name: str
    pattern: re.Pattern[str]
    severity: Severity
    description: str = ""


@dataclass(frozen=True, slots=True)
class Finding:
    """One suspected secret, at one location in one file.

    Findings are deliberately self-contained: severity is copied here rather
    than looked up from the rule, because entropy findings have no rule behind
    them, and JSON output may be read without access to the rule pack.

    Attributes:
        path: File the match was found in.
        line_number: 1-based line number, matching what an editor shows.
        rule_id: Identifier of the rule that matched.
        masked_secret: Masked preview of the match. This never holds the raw
            secret — an unmasked value must not exist as a field, so it cannot
            leak through a repr, a log line, or a traceback (NFR-3).
        severity: Copied from the matching rule.
        line_preview: Optional masked snippet of the surrounding line, for
            context in reports.
    """

    path: Path
    line_number: int
    rule_id: str
    masked_secret: str
    severity: Severity
    line_preview: str = ""


@dataclass(slots=True)
class ScanResult:
    """The outcome of a single scan: what was found, and what was walked.

    Mutable by design, unlike :class:`Rule` and :class:`Finding` — the scanner
    appends findings and increments counters as it walks the tree.

    Attributes:
        findings: Every suspected secret found, in discovery order.
        files_scanned: Number of files actually read.
        files_skipped: Number of files skipped as binary, unreadable, or
            oversized.
    """

    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    files_skipped: int = 0

    @property
    def has_findings(self) -> bool:
        """Whether the scan turned up at least one suspected secret."""
        return bool(self.findings)

    @property
    def exit_code(self) -> int:
        """Process exit status: 1 if anything was found, otherwise 0.

        This is what lets CI and the pre-commit hook fail a build (FR-11).
        """
        return 1 if self.has_findings else 0

    def count_by_severity(self) -> dict[Severity, int]:
        """Count findings per severity.

        Every severity is present, including those with a count of zero, so
        reporters can render a stable table without guarding for missing keys.
        """
        counts: dict[Severity, int] = dict.fromkeys(Severity, 0)
        for finding in self.findings:
            counts[finding.severity] += 1
        return counts

    def add(self, finding: Finding) -> None:
        """Record one finding."""
        self.findings.append(finding)
