from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Finding(BaseModel):
    title: str = Field(..., description="Short title for the finding")
    severity: Severity = Field(..., description="How serious the issue is")
    category: str = Field(
        ..., description="e.g. security, performance, scalability, SOLID, code_smell, duplication, bug, best_practice"
    )
    explanation: str = Field(..., description="Why this is an issue")
    recommended_fix: str = Field(..., description="Concrete, minimal fix - not a full rewrite")
    location: Optional[str] = Field(None, description="File/line/function if identifiable from the input")


class CodeReviewReport(BaseModel):
    summary: str = Field(..., description="2-3 sentence overview of the review")
    findings: List[Finding] = Field(..., description="Findings ordered from most to least severe")
