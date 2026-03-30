# Copyright since 2025 Mifos Initiative
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from unittest.mock import patch

from core.suggestion_engine import generate_suggestions
from mcp_server import get_overdue_loans_for_client


def test_overdue_loans_generates_expected_suggestions():
    data = [{"id": 101}, {"id": 101}]  # duplicate loan ID helps verify dedupe

    suggestions = generate_suggestions("get_overdue_loans", data)

    assert suggestions
    assert any("Apply a late fee" in item for item in suggestions)
    assert any("Send a repayment reminder" in item for item in suggestions)
    assert len(suggestions) <= 3


def test_active_loan_generates_repayment_schedule_suggestion():
    data = {"loanId": 1, "status": "Active"}

    suggestions = generate_suggestions("get_loan_details", data)

    assert any("View repayment schedule" in item for item in suggestions)


def test_empty_response_returns_empty_suggestions():
    assert generate_suggestions("get_overdue_loans", []) == []


def test_unknown_status_returns_empty_suggestions_without_crash():
    data = {"loanId": 1, "status": "Paused by external workflow"}

    suggestions = generate_suggestions("get_loan_details", data)

    assert suggestions == []


def test_overdue_wrapper_preserves_original_data_fields_and_adds_structured_suggestions():
    original = [
        {
            "id": 7,
            "status": "Active",
            "summary": {"totalOutstanding": 1500},
        }
    ]

    with patch("mcp_server.get_overdue_loans.func", return_value=original):
        result = get_overdue_loans_for_client(1)

    assert result["data"][0]["id"] == 7
    assert result["data"][0]["status"] == "Active"
    assert result["data"][0]["summary"] == {"totalOutstanding": 1500}

    # Non-breaking: legacy list[str] format still present.
    assert isinstance(result["suggestions"], list)
    assert result["suggestions"]

    # Additive improvement: structured suggestions are also exposed.
    assert isinstance(result["suggestions_structured"], list)
    assert result["suggestions_structured"][0].get("action_text")


def test_suggestions_are_deterministic_for_same_input():
    data = [{"id": 25}, {"id": 26}]

    first = generate_suggestions("get_overdue_loans", data)
    second = generate_suggestions("get_overdue_loans", data)

    assert first == second
