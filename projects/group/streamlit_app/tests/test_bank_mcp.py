from __future__ import annotations

from pathlib import Path

from bank_mcp.db import BankReviewRepository


def _repo(tmp_path: Path) -> BankReviewRepository:
    repo = BankReviewRepository(tmp_path / "bank_review_test.db")
    repo.initialize()
    return repo


def test_check_beneficiary_match_with_no_reports(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    result = repo.check_beneficiary(
        recipient_name="Apex Solutions Ltd",
        account_number="123-456-789-001",
    )

    assert result.to_dict() == {
        "name_account_check": "match",
        "reported_risk_status": "none",
    }


def test_check_beneficiary_high_risk_account(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    result = repo.check_beneficiary(
        recipient_name="Harbour View Trading Ltd",
        account_number="555666777003",
    )

    assert result.to_dict() == {
        "name_account_check": "match",
        "reported_risk_status": "high_risk",
    }


def test_report_duplicate_beneficiary_risk(tmp_path: Path) -> None:
    repo = _repo(tmp_path)

    first = repo.report_beneficiary_risk(
        account_number="123456789001",
        recipient_name="Apex Solutions Ltd",
        reason_code="manual_review",
        case_id="CASE-77",
    )
    second = repo.report_beneficiary_risk(
        account_number="123456789001",
        recipient_name="Apex Solutions Ltd",
        reason_code="manual_review",
        case_id="CASE-77",
    )

    assert first.status == "accepted"
    assert second.status == "duplicate"
    assert second.report_id == first.report_id
