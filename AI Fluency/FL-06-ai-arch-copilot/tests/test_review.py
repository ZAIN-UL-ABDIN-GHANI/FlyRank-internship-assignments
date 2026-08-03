import pytest
from pydantic import ValidationError

from app.review import CodeReviewReport, Finding, Severity


def test_valid_report_passes_validation():
    report = CodeReviewReport(
        summary="One SQL injection risk and one duplicated block found.",
        findings=[
            Finding(
                title="Unparameterized SQL query",
                severity=Severity.critical,
                category="security",
                explanation="User input is concatenated directly into the SQL string.",
                recommended_fix="Use parameterized queries or an ORM query builder.",
                location="db.py:42",
            )
        ],
    )
    assert report.findings[0].severity == Severity.critical


def test_invalid_severity_value_fails_validation():
    with pytest.raises(ValidationError):
        Finding(
            title="X",
            severity="super-bad",  # not a valid Severity enum value
            category="bug",
            explanation="...",
            recommended_fix="...",
        )


def test_report_missing_findings_fails_validation():
    with pytest.raises(ValidationError):
        CodeReviewReport(summary="No findings field provided")
