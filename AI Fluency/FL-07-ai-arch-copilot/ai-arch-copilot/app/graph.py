import logging
from typing import List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from app.config import settings
from app.diff_parser import format_files_for_review, looks_like_unified_diff, parse_unified_diff
from app.planning import ImplementationPlan
from app.retriever import Retriever
from app.review import CodeReviewReport

logger = logging.getLogger(__name__)

MAX_QUERY_CHARS = 2000  # embedding models have limited context; truncate long code before using it as a search query

SYSTEM_PROMPT = """You are a senior AI software engineer gathering requirements for a feature request.
Decide if the request below has enough detail to start a phased implementation plan (goal, inputs/outputs,
constraints, and scope). If anything essential is missing, ask exactly ONE concise clarifying question.
If the request is sufficiently specified, respond with exactly: READY

Do not propose code or a plan yet - this step only gathers requirements."""

PLANNING_PROMPT = """You are a senior AI software architect producing a phased implementation roadmap for
the feature request below. Follow these constraints strictly:
- Keep phases small, sequential, and independently verifiable.
- Prefer minimal dependencies; avoid overengineering.
- Do not include features beyond what was requested.
- Ground the tech stack and design in the provided project rules/context where relevant.

Feature request (from conversation):
{conversation}

Relevant project rules/context:
{context}
"""

CODE_REVIEW_PROMPT = """You are a senior AI code reviewer. Review the code or diff below for architecture,
code quality, security, performance, scalability, and adherence to SOLID principles and the project's
Development Rules. Detect bugs, code smells, duplication, and rule violations.

Order findings from most to least severe. Each finding needs a clear explanation and a concrete,
minimal recommended fix - do not suggest full rewrites for isolated issues.

Code, diff, or files to review:
{code}

Relevant project rules/best-practice context:
{context}
"""


class AgentState(TypedDict):
    history: List[dict]
    retrieved_context: List[str]
    clarifying_question: Optional[str]
    requirements_complete: bool
    plan: Optional[dict]
    code_context: Optional[str]
    code_files: Optional[List[dict]]
    review: Optional[dict]


def _build_llm():
    return ChatGoogleGenerativeAI(
        model=settings.google_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    )


_retriever: Retriever = None


def _get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def retrieve_context(state: AgentState) -> AgentState:
    query = state["history"][-1]["content"] if state["history"] else ""
    try:
        results = _get_retriever().search(query, top_k=3)
        state["retrieved_context"] = [r["text"] for r in results]
        logger.info("retrieve_context: found %d chunks", len(state["retrieved_context"]))
    except FileNotFoundError:
        # No index built yet - proceed without context rather than failing the request.
        state["retrieved_context"] = []
        logger.warning("retrieve_context: no FAISS index found, proceeding without context")
    return state


def gather_requirements(state: AgentState) -> AgentState:
    llm = _build_llm()
    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in state["history"])

    system_prompt = SYSTEM_PROMPT
    if state.get("retrieved_context"):
        rules_block = "\n---\n".join(state["retrieved_context"])
        system_prompt += f"\n\nRelevant project rules/context:\n{rules_block}"

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=conversation)]
    reply = llm.invoke(messages).content.strip()

    if reply == "READY":
        state["requirements_complete"] = True
        state["clarifying_question"] = None
    else:
        state["requirements_complete"] = False
        state["clarifying_question"] = reply
    logger.info("gather_requirements: complete=%s", state["requirements_complete"])
    return state


def _build_planning_llm():
    return _build_llm().with_structured_output(ImplementationPlan)


def generate_plan(state: AgentState) -> AgentState:
    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in state["history"])
    context = "\n---\n".join(state.get("retrieved_context", [])) or "(none retrieved)"
    prompt = PLANNING_PROMPT.format(conversation=conversation, context=context)

    llm = _build_planning_llm()
    plan: ImplementationPlan = llm.invoke(prompt)
    state["plan"] = plan.model_dump()
    logger.info("generate_plan: produced %d phases", len(plan.phases))
    return state


def _build_review_llm():
    return _build_llm().with_structured_output(CodeReviewReport)


def review_code(state: AgentState) -> AgentState:
    code = state.get("code_context")
    files = state.get("code_files")

    if not code and not files:
        state["review"] = None
        return state

    if files:
        formatted_code = format_files_for_review(files)
    elif looks_like_unified_diff(code):
        try:
            formatted_code = format_files_for_review(parse_unified_diff(code))
        except ValueError:
            logger.warning("review_code: input looked like a diff but failed to parse, reviewing as raw text")
            formatted_code = code
    else:
        formatted_code = code

    try:
        query = formatted_code[:MAX_QUERY_CHARS]
        code_matches = _get_retriever().search(query, top_k=3)
        code_related_context = [r["text"] for r in code_matches]
    except FileNotFoundError:
        code_related_context = []

    combined = list(dict.fromkeys(state.get("retrieved_context", []) + code_related_context))
    context_block = "\n---\n".join(combined) or "(none retrieved)"

    prompt = CODE_REVIEW_PROMPT.format(code=formatted_code, context=context_block)
    llm = _build_review_llm()
    report: CodeReviewReport = llm.invoke(prompt)
    state["review"] = report.model_dump()
    logger.info("review_code: %d findings", len(report.findings))
    return state


def _route_after_requirements(state: AgentState) -> str:
    return "generate_plan" if state["requirements_complete"] else "end"


def _route_after_plan(state: AgentState) -> str:
    return "review_code" if (state.get("code_context") or state.get("code_files")) else "end"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("gather_requirements", gather_requirements)
    graph.add_node("generate_plan", generate_plan)
    graph.add_node("review_code", review_code)
    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "gather_requirements")
    graph.add_conditional_edges(
        "gather_requirements",
        _route_after_requirements,
        {"generate_plan": "generate_plan", "end": END},
    )
    graph.add_conditional_edges(
        "generate_plan",
        _route_after_plan,
        {"review_code": "review_code", "end": END},
    )
    graph.add_edge("review_code", END)
    return graph.compile()
