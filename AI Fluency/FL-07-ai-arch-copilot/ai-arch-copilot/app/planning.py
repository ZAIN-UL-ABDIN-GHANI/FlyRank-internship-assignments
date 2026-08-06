from typing import List

from pydantic import BaseModel, Field


class PlanPhase(BaseModel):
    name: str = Field(..., description="Short phase name, e.g. 'Phase 1: Core API'")
    goal: str = Field(..., description="One-sentence goal for this phase")
    tasks: List[str] = Field(..., description="3-6 concrete, small implementation tasks")


class ImplementationPlan(BaseModel):
    system_design: str = Field(..., description="2-4 sentence summary of the architecture")
    tech_stack: List[str] = Field(..., description="Concrete technologies/libraries to use, minimal set")
    phases: List[PlanPhase] = Field(..., description="2-5 small, sequential implementation phases")
