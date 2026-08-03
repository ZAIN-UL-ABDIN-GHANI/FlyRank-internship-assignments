from unittest.mock import MagicMock, patch

import app.graph as graph_module
from app.graph import build_graph, gather_requirements, retrieve_context


def _mock_llm(reply_text):
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content=reply_text)
    return mock


class _FakeRetriever:
    def __init__(self, chunks):
        self._chunks = chunks

    def search(self, query, top_k=3):
        return self._chunks


@patch("app.graph._build_llm")
def test_incomplete_request_asks_one_question(mock_build_llm):
    mock_build_llm.return_value = _mock_llm("What should be cached, and for how long?")
    graph = build_graph()
    state = {
        "history": [{"role": "user", "content": "add caching"}],
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": False,
    }
    with patch("app.graph._get_retriever", side_effect=FileNotFoundError):
        result = graph.invoke(state)
    assert result["requirements_complete"] is False
    assert result["clarifying_question"] == "What should be cached, and for how long?"


@patch("app.graph._build_llm")
def test_complete_request_is_marked_ready(mock_build_llm):
    mock_build_llm.return_value = _mock_llm("READY")
    graph = build_graph()
    state = {
        "history": [
            {
                "role": "user",
                "content": "Cache GET /users responses in Redis for 5 minutes, keyed by query params.",
            }
        ],
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": False,
    }
    with patch("app.graph._get_retriever", side_effect=FileNotFoundError):
        result = graph.invoke(state)
    assert result["requirements_complete"] is True
    assert result["clarifying_question"] is None


def test_retrieve_context_falls_back_to_empty_when_no_index():
    state = {
        "history": [{"role": "user", "content": "anything"}],
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": False,
    }
    with patch("app.graph._get_retriever", side_effect=FileNotFoundError):
        result = retrieve_context(state)
    assert result["retrieved_context"] == []


def test_retrieve_context_populates_state_from_retriever():
    graph_module._retriever = _FakeRetriever(
        [{"source": "development_rules.md", "text": "Never implement unapproved features.", "score": 0.9}]
    )
    state = {
        "history": [{"role": "user", "content": "add a new unrequested feature"}],
        "retrieved_context": [],
        "clarifying_question": None,
        "requirements_complete": False,
    }
    result = retrieve_context(state)
    graph_module._retriever = None  # reset singleton for other tests
    assert result["retrieved_context"] == ["Never implement unapproved features."]


@patch("app.graph._build_llm")
def test_retrieved_context_is_passed_into_llm_prompt(mock_build_llm):
    llm = _mock_llm("READY")
    mock_build_llm.return_value = llm

    state = {
        "history": [{"role": "user", "content": "add a new unrequested feature"}],
        "retrieved_context": ["Never implement unapproved features."],
        "clarifying_question": None,
        "requirements_complete": False,
    }
    gather_requirements(state)

    system_message = llm.invoke.call_args[0][0][0]
    assert "Never implement unapproved features." in system_message.content
