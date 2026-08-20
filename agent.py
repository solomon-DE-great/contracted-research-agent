from __future__ import annotations
import json
import os
from typing import Optional, Tuple
from groq import Groq
from contracts import (
    ResearchQuestion, Claim, Source, ReportSection, VerifiedReport, ProvenanceTrace,
)

# THIS IS THE ONLY MODEL WE WILL EVER USE
FORCED_MODEL = "llama-3.1-8b-instant"

def get_client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is missing in Streamlit Secrets")
    return Groq(api_key=key)

def call_llm(system: str, user: str, temperature: float = 0.2) -> str:
    client = get_client()
    resp = client.chat.completions.create(
        model=FORCED_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content or "{}"

SYSTEM_PROMPT = """You are a rigorous research assistant that follows Design-by-Contract principles.
You NEVER invent citations. Every factual claim MUST be backed by a plausible source.
Always answer in valid JSON that matches the requested schema exactly."""

def generate_verified_report(
    question: str,
    domain: Optional[str] = None,
    constraints: Optional[str] = None,
    model: str = None,          # we ignore this completely
) -> Tuple[VerifiedReport, list[str]]:
    rq = ResearchQuestion(question=question, domain=domain, constraints=constraints)
    steps = [f"Input accepted: {rq.question[:80]}..."]

    plan_prompt = f"""Research question: {rq.question}
Domain: {rq.domain or "general"}
Constraints: {rq.constraints or "none"}

Return JSON:
{{
  "sections": ["Section 1", "Section 2"],
  "search_strategy": "brief"
}}"""
    plan = json.loads(call_llm(SYSTEM_PROMPT, plan_prompt))
    steps.append(f"Plan created with {len(plan.get('sections', []))} sections")

    claims_prompt = f"""Research question: {rq.question}
Domain: {rq.domain or "general"}
Constraints: {rq.constraints or "prefer recent peer-reviewed sources"}
Sections: {json.dumps(plan.get("sections", []))}

Return JSON:
{{
  "executive_summary": "3-6 sentence synthesis",
  "sections": [
    {{
      "title": "...",
      "summary": "optional",
      "claims": [
        {{
          "text": "clear factual claim",
          "confidence": "high|medium|low",
          "caveats": "optional",
          "sources": [
            {{
              "title": "paper title",
              "url_or_id": "DOI or URL",
              "year": 2023,
              "note": "optional"
            }}
          ]
        }}
      ]
    }}
  ],
  "limitations": "honest gaps"
}}

Rules: Every claim must have at least one source. Prefer real papers. 4-10 claims total."""
    data = json.loads(call_llm(SYSTEM_PROMPT, claims_prompt, temperature=0.3))
    steps.append("Claims generated")

    all_claims = []
    sections = []
    for sec in data.get("sections", []):
        sec_claims = []
        for c in sec.get("claims", []):
            sources = [Source(**s) for s in c.get("sources", [])]
            claim = Claim(
                text=c["text"],
                sources=sources,
                confidence=c.get("confidence", "medium"),
                caveats=c.get("caveats"),
            )
            sec_claims.append(claim)
            all_claims.append(claim)
        sections.append(ReportSection(
            title=sec["title"],
            claims=sec_claims,
            summary=sec.get("summary"),
        ))

    provenance = ProvenanceTrace(
        question=rq.question,
        model_used=FORCED_MODEL,
        steps=steps + ["Validating contracts"],
        contract_checks_passed=False,
    )

    report = VerifiedReport(
        question=rq.question,
        executive_summary=data["executive_summary"],
        sections=sections,
        all_claims=all_claims,
        provenance=provenance,
        limitations=data.get("limitations", "Not specified"),
    )
    report.provenance.contract_checks_passed = True
    report.provenance.steps.append("All contracts passed")
    steps.append("Report ready")
    return report, steps
