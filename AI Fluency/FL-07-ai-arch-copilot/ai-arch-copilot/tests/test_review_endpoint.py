from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.review import CodeReviewReport, Finding, Severity

client = TestClient(app)


def _sample_report():
    return CodeReviewReport(
        summary="One security issue found.",
        findings=[
            Finding(
                title="Unparameterized SQL query",
                severity=Severity.critical,
                category="security",
                explanation="User input concatenated into SQL string.",
                recommended_fix="Use parameterized queries.",
                location="db.py:1",
            )
        ],
    )


def test_review_requires_code_or_files():
    r = client.post("/agent/review", json={})
    assert r.status_code == 400


def test_review_rejects_empty_files_list_and_no_code():
    r = client.post("/agent/review", json={"files": []})
    assert r.status_code == 400


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_review_llm")
def test_review_with_raw_code_returns_report(mock_build_review_llm, mock_get_retriever):
    mock_build_review_llm.return_value.invoke.return_value = _sample_report()

    r = client.post(
        "/agent/review",
        json={"code": "query = f\"SELECT * FROM users WHERE id={user_id}\""},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["review"]["findings"][0]["severity"] == "critical"


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_review_llm")
def test_review_with_multiple_files_formats_with_file_boundaries(mock_build_review_llm, mock_get_retriever):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = _sample_report()
    mock_build_review_llm.return_value = mock_llm

    r = client.post(
        "/agent/review",
        json={
            "files": [
                {"filename": "db.py", "content": "query = f\"SELECT * FROM users WHERE id={user_id}\""},
                {"filename": "utils.py", "content": "def helper():\n    pass"},
            ]
        },
    )
    assert r.status_code == 200
    prompt_sent = mock_llm.invoke.call_args[0][0]
    assert "=== FILE: db.py ===" in prompt_sent
    assert "=== FILE: utils.py ===" in prompt_sent


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_review_llm")
def test_review_with_git_diff_parses_per_file(mock_build_review_llm, mock_get_retriever):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = _sample_report()
    mock_build_review_llm.return_value = mock_llm

    diff_text = (
        "diff --git a/db.py b/db.py\n"
        "index 83db48f..bf269f4 100644\n"
        "--- a/db.py\n"
        "+++ b/db.py\n"
        "@@ -1,3 +1,3 @@\n"
        " def get_user(user_id):\n"
        '-    query = "SELECT * FROM users WHERE id=" + user_id\n'
        '+    query = f"SELECT * FROM users WHERE id={user_id}"\n'
        "     return db.execute(query)\n"
    )
    r = client.post("/agent/review", json={"code": diff_text})
    assert r.status_code == 200
    prompt_sent = mock_llm.invoke.call_args[0][0]
    assert "=== FILE: db.py ===" in prompt_sent


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_review_llm")
def test_review_llm_failure_returns_502(mock_build_review_llm, mock_get_retriever):
    mock_build_review_llm.return_value.invoke.side_effect = RuntimeError("model unavailable")

    r = client.post("/agent/review", json={"code": "print('hi')"})
    assert r.status_code == 502
    assert "code review failed" in r.json()["detail"]


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_planning_llm")
@patch("app.graph._build_llm")
@patch("app.graph._build_review_llm")
def test_review_never_calls_requirements_or_planning_llms(
    mock_build_review_llm, mock_build_llm, mock_build_planning_llm, mock_get_retriever
):
    mock_build_review_llm.return_value.invoke.return_value = _sample_report()

    r = client.post("/agent/review", json={"code": "print('hi')"})
    assert r.status_code == 200
    mock_build_llm.assert_not_called()
    mock_build_planning_llm.assert_not_called()
