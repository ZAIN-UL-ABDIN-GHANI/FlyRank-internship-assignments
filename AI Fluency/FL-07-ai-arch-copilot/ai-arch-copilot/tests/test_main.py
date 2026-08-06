from unittest.mock import MagicMock, patch

import app.session_store as session_store
from fastapi.testclient import TestClient

from app.main import app
from app.planning import ImplementationPlan, PlanPhase


def _sample_plan():
    return ImplementationPlan(
        system_design="Minimal FastAPI + LangGraph service.",
        tech_stack=["FastAPI", "LangGraph"],
        phases=[PlanPhase(name="Phase 1", goal="Ship the core", tasks=["Build endpoint", "Write test"])],
    )


def _client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "sessions.db")
    monkeypatch.setattr(session_store.settings, "session_db_path", db_path)
    return TestClient(app)


def test_empty_message_returns_400(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    r = client.post("/agent/gather", json={"session_id": "s1", "message": "   "})
    assert r.status_code == 400


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_planning_llm")
@patch("app.graph._build_llm")
def test_second_call_same_session_sees_first_messages(
    mock_build_llm, mock_build_planning_llm, mock_get_retriever, tmp_path, monkeypatch
):
    client = _client(tmp_path, monkeypatch)

    gather_mock = MagicMock()
    gather_mock.invoke.return_value = MagicMock(content="What should be cached, and for how long?")
    mock_build_llm.return_value = gather_mock

    planning_mock = MagicMock()
    planning_mock.invoke.return_value = _sample_plan()
    mock_build_planning_llm.return_value = planning_mock

    r1 = client.post("/agent/gather", json={"session_id": "s1", "message": "add caching"})
    assert r1.status_code == 200
    assert r1.json()["clarifying_question"] == "What should be cached, and for how long?"

    gather_mock.invoke.return_value = MagicMock(content="READY")
    r2 = client.post(
        "/agent/gather",
        json={"session_id": "s1", "message": "Cache GET /users in Redis for 5 minutes."},
    )
    assert r2.status_code == 200
    assert r2.json()["requirements_complete"] is True

    # The conversation the LLM saw on the second call must include the first turn.
    second_call_prompt = gather_mock.invoke.call_args[0][0][1].content
    assert "add caching" in second_call_prompt


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_planning_llm")
@patch("app.graph._build_llm")
def test_new_session_id_starts_with_empty_history(
    mock_build_llm, mock_build_planning_llm, mock_get_retriever, tmp_path, monkeypatch
):
    client = _client(tmp_path, monkeypatch)
    gather_mock = MagicMock()
    gather_mock.invoke.return_value = MagicMock(content="READY")
    mock_build_llm.return_value = gather_mock
    mock_build_planning_llm.return_value.invoke.return_value = _sample_plan()

    client.post("/agent/gather", json={"session_id": "existing", "message": "first session message"})

    client.post("/agent/gather", json={"session_id": "brand-new", "message": "hello"})
    prompt = gather_mock.invoke.call_args[0][0][1].content
    assert "first session message" not in prompt


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_planning_llm")
@patch("app.graph._build_llm")
def test_reset_clears_session_history(
    mock_build_llm, mock_build_planning_llm, mock_get_retriever, tmp_path, monkeypatch
):
    client = _client(tmp_path, monkeypatch)
    gather_mock = MagicMock()
    gather_mock.invoke.return_value = MagicMock(content="READY")
    mock_build_llm.return_value = gather_mock
    mock_build_planning_llm.return_value.invoke.return_value = _sample_plan()

    client.post("/agent/gather", json={"session_id": "s1", "message": "add caching"})
    r = client.post("/session/s1/reset")
    assert r.status_code == 200
    assert r.json() == {"session_id": "s1", "reset": True}

    client.post("/agent/gather", json={"session_id": "s1", "message": "hello again"})
    prompt = gather_mock.invoke.call_args[0][0][1].content
    assert "add caching" not in prompt


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_review_llm")
@patch("app.graph._build_planning_llm")
@patch("app.graph._build_llm")
def test_agent_gather_reviews_multiple_files_end_to_end(
    mock_build_llm, mock_build_planning_llm, mock_build_review_llm, mock_get_retriever, tmp_path, monkeypatch
):
    from app.planning import ImplementationPlan, PlanPhase
    from app.review import CodeReviewReport, Finding, Severity

    client = _client(tmp_path, monkeypatch)

    gather_mock = MagicMock()
    gather_mock.invoke.return_value = MagicMock(content="READY")
    mock_build_llm.return_value = gather_mock

    mock_build_planning_llm.return_value.invoke.return_value = ImplementationPlan(
        system_design="x", tech_stack=["FastAPI"], phases=[PlanPhase(name="P1", goal="g", tasks=["t"])]
    )

    review_mock = MagicMock()
    review_mock.invoke.return_value = CodeReviewReport(
        summary="Reviewed two files.",
        findings=[
            Finding(
                title="Unparameterized SQL",
                severity=Severity.critical,
                category="security",
                explanation="Raw string interpolation into SQL.",
                recommended_fix="Use parameterized queries.",
                location="db.py:1",
            )
        ],
    )
    mock_build_review_llm.return_value = review_mock

    r = client.post(
        "/agent/gather",
        json={
            "session_id": "s1",
            "message": "Cache GET /users in Redis for 5 minutes.",
            "files": [
                {"filename": "db.py", "content": "query = f\"SELECT * FROM users WHERE id={user_id}\""},
                {"filename": "utils.py", "content": "def helper():\n    pass"},
            ],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["requirements_complete"] is True
    assert body["review"]["summary"] == "Reviewed two files."

    prompt_sent = review_mock.invoke.call_args[0][0]
    assert "=== FILE: db.py ===" in prompt_sent
    assert "=== FILE: utils.py ===" in prompt_sent
