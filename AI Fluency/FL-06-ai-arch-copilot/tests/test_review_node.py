from unittest.mock import MagicMock, patch

from app.graph import build_graph, review_code
from app.planning import ImplementationPlan, PlanPhase
from app.review import CodeReviewReport, Finding, Severity


def _sample_plan():
    return ImplementationPlan(
        system_design="Minimal FastAPI + LangGraph service.",
        tech_stack=["FastAPI", "LangGraph"],
        phases=[PlanPhase(name="Phase 1", goal="Ship the core", tasks=["Build endpoint", "Write test"])],
    )


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
                location="db.py:10",
            )
        ],
    )


def test_review_code_skips_when_no_code_provided():
    state = {
        "history": [],
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": True,
        "plan": None,
        "code_context": None,
        "review": None,
    }
    result = review_code(state)
    assert result["review"] is None


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_review_llm")
def test_review_code_populates_state_when_code_provided(mock_build_review_llm, mock_get_retriever):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = _sample_report()
    mock_build_review_llm.return_value = mock_llm

    state = {
        "history": [],
        "retrieved_context": ["Never silently ignore exceptions."],
        "clarifying_question": None,
        "requirements_complete": True,
        "plan": None,
        "code_context": "query = f\"SELECT * FROM users WHERE id={user_id}\"",
        "review": None,
    }
    result = review_code(state)
    assert result["review"]["findings"][0]["severity"] == "critical"
    assert result["review"]["findings"][0]["category"] == "security"


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_planning_llm")
@patch("app.graph._build_llm")
def test_graph_skips_review_when_no_code_provided(mock_build_llm, mock_build_planning_llm, mock_get_retriever):
    gather_mock = MagicMock()
    gather_mock.invoke.return_value = MagicMock(content="READY")
    mock_build_llm.return_value = gather_mock

    planning_mock = MagicMock()
    planning_mock.invoke.return_value = _sample_plan()
    mock_build_planning_llm.return_value = planning_mock

    graph = build_graph()
    state = {
        "history": [{"role": "user", "content": "Cache GET /users responses in Redis for 5 minutes."}],
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": False,
        "plan": None,
        "code_context": None,
        "review": None,
    }
    result = graph.invoke(state)
    assert result["plan"] is not None
    assert result["review"] is None


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_review_llm")
@patch("app.graph._build_planning_llm")
@patch("app.graph._build_llm")
def test_graph_runs_review_when_code_provided(
    mock_build_llm, mock_build_planning_llm, mock_build_review_llm, mock_get_retriever
):
    gather_mock = MagicMock()
    gather_mock.invoke.return_value = MagicMock(content="READY")
    mock_build_llm.return_value = gather_mock

    planning_mock = MagicMock()
    planning_mock.invoke.return_value = _sample_plan()
    mock_build_planning_llm.return_value = planning_mock

    review_mock = MagicMock()
    review_mock.invoke.return_value = _sample_report()
    mock_build_review_llm.return_value = review_mock

    graph = build_graph()
    state = {
        "history": [{"role": "user", "content": "Cache GET /users responses in Redis for 5 minutes."}],
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": False,
        "plan": None,
        "code_context": "query = f\"SELECT * FROM users WHERE id={user_id}\"",
        "review": None,
    }
    result = graph.invoke(state)
    assert result["plan"]["tech_stack"] == ["FastAPI", "LangGraph"]
    assert result["review"]["summary"] == "One security issue found."
