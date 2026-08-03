import pytest
from pydantic import ValidationError

from app.planning import ImplementationPlan, PlanPhase


def test_valid_plan_passes_validation():
    plan = ImplementationPlan(
        system_design="A FastAPI service with a LangGraph pipeline for requirements and planning.",
        tech_stack=["FastAPI", "LangGraph", "LangChain", "FAISS"],
        phases=[
            PlanPhase(
                name="Phase 1: API skeleton",
                goal="Expose a working endpoint",
                tasks=["Create FastAPI app", "Add health check"],
            )
        ],
    )
    assert plan.phases[0].name == "Phase 1: API skeleton"
    assert len(plan.tech_stack) == 4


def test_plan_missing_required_field_fails_validation():
    with pytest.raises(ValidationError):
        ImplementationPlan(tech_stack=["FastAPI"], phases=[])  # missing system_design


def test_phase_missing_tasks_fails_validation():
    with pytest.raises(ValidationError):
        PlanPhase(name="Phase 1", goal="Do the thing")  # missing tasks
