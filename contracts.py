"""
Design-by-Contract data models for the Verifiable Research Agent.

These models enforce structure and provenance *by construction*,
mirroring the philosophy of SymbolicAI contracts (ExtensityAI).
Every Claim must carry a source; the final Report must pass validation
before it is returned to the user.
"""

from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime


class Source(BaseModel):
    """A single evidence source with minimal required provenance."""
    title: str = Field(..., min_length=3, description="Title of the paper, page or document")
    url_or_id: str = Field(..., description="URL, DOI, arXiv ID or other stable identifier")
    year: Optional[int] = Field(None, ge=1900, le=2030)
    note: Optional[str] = Field(None, description="Short note on relevance or limitations")

    @field_validator("url_or_id")
    @classmethod
    def must_look_like_identifier(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Source identifier too short")
        return v


class Claim(BaseModel):
    """
    Atomic claim that must be backed by at least one Source.
    This is the core contract: no claim without evidence.
    """
    text: str = Field(..., min_length=10, description="The factual statement")
    sources: List[Source] = Field(..., min_length=1, description="Supporting evidence")
    confidence: Literal["high", "medium", "low"] = "medium"
    caveats: Optional[str] = Field(None, description="Limitations or conflicting evidence")

    @model_validator(mode="after")
    def at_least_one_source(self) -> "Claim":
        if not self.sources:
            raise ValueError("Contract violation: Claim must have ≥1 Source")
        return self


class ResearchQuestion(BaseModel):
    """Input contract."""
    question: str = Field(..., min_length=10)
    domain: Optional[str] = Field(None, description="e.g. neuroscience, climate, software engineering")
    constraints: Optional[str] = Field(
        None,
        description="e.g. 'only peer-reviewed 2020+, prefer RCTs, max 8 claims'"
    )


class ReportSection(BaseModel):
    title: str
    claims: List[Claim] = Field(default_factory=list)
    summary: Optional[str] = None


class ProvenanceTrace(BaseModel):
    """Full audit trail for one generation run."""
    question: str
    model_used: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    steps: List[str] = Field(default_factory=list)
    contract_checks_passed: bool = False
    notes: Optional[str] = None


class VerifiedReport(BaseModel):
    """
    Final output contract.
    The agent is not allowed to return a report that fails these checks.
    """
    question: str
    executive_summary: str = Field(..., min_length=50)
    sections: List[ReportSection] = Field(..., min_length=1)
    all_claims: List[Claim] = Field(..., min_length=1)
    provenance: ProvenanceTrace
    limitations: str = Field(..., min_length=20)

    @model_validator(mode="after")
    def every_claim_has_source(self) -> "VerifiedReport":
        for claim in self.all_claims:
            if not claim.sources:
                raise ValueError("Contract violation: orphan claim without sources")
        if not self.sections:
            raise ValueError("Contract violation: report must contain sections")
        return self

    def to_markdown(self) -> str:
        lines = [
            f"# Verified Research Report",
            f"**Question:** {self.question}",
            f"**Generated:** {self.provenance.timestamp}",
            f"**Model:** {self.provenance.model_used}",
            "",
            "## Executive Summary",
            self.executive_summary,
            "",
        ]
        for sec in self.sections:
            lines.append(f"## {sec.title}")
            if sec.summary:
                lines.append(sec.summary)
                lines.append("")
            for i, claim in enumerate(sec.claims, 1):
                lines.append(f"**Claim {i}** ({claim.confidence} confidence)")
                lines.append(claim.text)
                if claim.caveats:
                    lines.append(f"*Caveats:* {claim.caveats}")
                lines.append("Sources:")
                for s in claim.sources:
                    year = f" ({s.year})" if s.year else ""
                    lines.append(f"- {s.title}{year} — `{s.url_or_id}`")
                    if s.note:
                        lines.append(f"  _{s.note}_")
                lines.append("")
        lines.extend([
            "## Limitations",
            self.limitations,
            "",
            "---",
            "*This report was generated under Design-by-Contract constraints. "
            "Every claim carries explicit provenance. "
            "Inspired by ExtensityAI SymbolicAI contracts.*",
        ])
        return "\n".join(lines)
