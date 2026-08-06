from unittest.mock import MagicMock, patch

from app.graph import build_graph, generate_plan
from app.planning import ImplementationPlan, PlanPhase


def _sample_plan():
    return ImplementationPlan(
        system_design="Minimal FastAPI + LangGraph service.",
        tech_stack=["FastAPI", "LangGraph"],
        phases=[PlanPhase(name="Phase 1", goal="Ship the core", tasks=["Build endpoint", "Write test"])],
    )


@patch("app.graph._build_planning_llm")
def test_generate_plan_populates_state(mock_build_planning_llm):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = _sample_plan()
    mock_build_planning_llm.return_value = mock_llm

    state = {
        "history": [{"role": "user", "content": "Cache GET /users responses in Redis for 5 minutes."}],
        "retrieved_context": ["Keep phases small and sequential."],
        "clarifying_question": None,
        "requirements_complete": True,
        "plan": None,
    }
    result = generate_plan(state)
    assert result["plan"]["tech_stack"] == ["FastAPI", "LangGraph"]
    assert result["plan"]["phases"][0]["name"] == "Phase 1"


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_llm")
@patch("app.graph._build_planning_llm")
def test_graph_skips_planning_when_requirements_incomplete(
    mock_build_planning_llm, mock_build_llm, mock_get_retriever
):
    gather_mock = MagicMock()
    gather_mock.invoke.return_value = MagicMock(content="What should be cached?")
    mock_build_llm.return_value = gather_mock

    graph = build_graph()
    state = {
        "history": [{"role": "user", "content": "add caching"}],
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": False,
        "plan": None,
    }
    result = graph.invoke(state)

    assert result["requirements_complete"] is False
    assert result["plan"] is None
    mock_build_planning_llm.assert_not_called()


@patch("app.graph._get_retriever", side_effect=FileNotFoundError)
@patch("app.graph._build_llm")
@patch("app.graph._build_planning_llm")
def test_graph_runs_planning_when_requirements_complete(
    mock_build_planning_llm, mock_build_llm, mock_get_retriever
):
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
    }
    result = graph.invoke(state)

    assert result["requirements_complete"] is True
    assert result["plan"]["tech_stack"] == ["FastAPI", "LangGraph"]
    assert result["plan"]["phases"][0]["goal"] == "Ship the core"
