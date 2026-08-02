"""Tests for the core data types.

These pin down the decisions in models.py that other modules rely on: that rules
and findings are immutable and hashable, that a scan result is mutable, and that
exit codes follow FR-11.
"""

import json
import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from credsniff.models import Finding, Rule, ScanResult, Severity

AWS_PATTERN = re.compile(r"AKIA[0-9A-Z]{16}")


# --------------------------------------------------------------------- Severity


@pytest.mark.parametrize(
    ("severity", "expected_rank"),
    [(Severity.LOW, 1), (Severity.MEDIUM, 2), (Severity.HIGH, 3), (Severity.CRITICAL, 4)],
)
def test_severity_rank(severity: Severity, expected_rank: int) -> None:
    """Test that the rank property returns the expected numeric severity."""
    assert severity.rank == expected_rank


def test_every_severity_has_a_rank() -> None:
    """Guard against adding a Severity member and forgetting to rank it."""
    for severity in Severity:
        assert severity.rank > 0


def test_severity_serialization() -> None:
    """StrEnum members serialise as plain strings, with no custom encoder (FR-10)."""
    assert json.dumps({"severity": Severity.HIGH}) == '{"severity": "high"}'


def test_severity_rank_ordering() -> None:
    """Test that the rank property orders severities correctly."""
    severities = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
    sorted_severities = sorted(severities, key=lambda s: s.rank)
    assert sorted_severities == severities


# ------------------------------------------------------------------------- Rule


def make_rule(rule_id: str = "aws-access-key-id") -> Rule:
    """Build a rule varing only with id."""
    return Rule(
        id=rule_id,
        name="AWS Access Key ID",
        pattern=AWS_PATTERN,
        severity=Severity.HIGH,
        description="Detects AWS access key IDs.",
    )


def test_rule_immutable() -> None:
    """Test that Rule instances are immutable."""
    rule = make_rule()
    with pytest.raises(FrozenInstanceError):
        rule.severity = Severity.MEDIUM  # type: ignore[misc]


def test_rules_are_hashable() -> None:
    """Test that Rule instances are hashable."""
    assert len({make_rule("a"), make_rule("b")}) == 2


def test_equal_rules_deduplicate() -> None:
    """Test that equal Rule instances are considered the same in a set."""
    rule1 = make_rule("aws-access-key-id")
    rule2 = make_rule("aws-access-key-id")
    assert rule1 == rule2
    assert len({rule1, rule2}) == 1


# ---------------------------------------------------------------------- Finding


def make_finding(line_number: int = 1, severity: Severity = Severity.HIGH) -> Finding:
    """Build a finding, varying only line number and severity."""
    return Finding(
        path=Path("example.txt"),
        line_number=line_number,
        rule_id="aws-access-key-id",
        masked_secret="AKIA************",
        severity=severity,
    )


def test_finding_immutable() -> None:
    """Findings are records of what was seen, never edited after the fact."""
    finding = make_finding()
    with pytest.raises(FrozenInstanceError):
        finding.line_number = 99  # type: ignore[misc]


def test_equal_findings_deduplicate() -> None:
    """The same secret found twice collapses to one entry in a set."""
    assert len({make_finding(1), make_finding(1)}) == 1
    assert len({make_finding(1), make_finding(2)}) == 2


# ------------------------------------------------------------------- ScanResult


def test_new_scan_result_is_empty() -> None:
    """A scan result is constructible with no arguments and starts clean."""
    result = ScanResult()
    assert result.findings == []
    assert result.files_scanned == 0
    assert result.files_skipped == 0


def test_scan_results_do_not_share_a_findings_list() -> None:
    """field(default_factory=list) gives each instance its own list.

    A bare `findings: list[Finding] = []` default would share one list across
    every instance — the classic mutable-default bug.
    """
    first, second = ScanResult(), ScanResult()
    first.add(make_finding())
    assert first.findings != []
    assert second.findings == []


def test_counters_are_mutable() -> None:
    """ScanResult is deliberately NOT frozen: the scanner increments as it walks."""
    result = ScanResult()
    result.files_scanned += 1
    result.files_skipped += 2
    assert result.files_scanned == 1
    assert result.files_skipped == 2


def test_add_records_the_finding() -> None:
    """Test that add appends to the findings list."""
    result = ScanResult()
    finding = make_finding()
    result.add(finding)
    assert result.findings == [finding]


def test_has_findings() -> None:
    """Test that has_findings reflects whether anything was recorded."""
    result = ScanResult()
    assert result.has_findings is False
    result.add(make_finding())
    assert result.has_findings is True


def test_exit_code_is_zero_when_clean() -> None:
    """Exit 0 on a clean scan, so CI and the pre-commit hook pass (FR-11)."""
    assert ScanResult().exit_code == 0


def test_exit_code_is_one_when_secrets_found() -> None:
    """Exit 1 on any finding — this is what fails the build (FR-11)."""
    result = ScanResult()
    result.add(make_finding())
    assert result.exit_code == 1


def test_count_by_severity_counts_each_severity() -> None:
    """Test that findings are tallied against the right severity."""
    result = ScanResult()
    result.add(make_finding(1, Severity.HIGH))
    result.add(make_finding(2, Severity.HIGH))
    result.add(make_finding(3, Severity.CRITICAL))

    counts = result.count_by_severity()

    assert counts[Severity.HIGH] == 2
    assert counts[Severity.CRITICAL] == 1
    assert counts[Severity.LOW] == 0


def test_count_by_severity_includes_every_severity() -> None:
    """Absent severities report zero, so reporters never guard for missing keys."""
    counts = ScanResult().count_by_severity()
    assert counts == dict.fromkeys(Severity, 0)
