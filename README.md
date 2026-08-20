# Contracted Research Agent

**Zero-cost, Design-by-Contract research automation demo**  
Inspired by [ExtensityAI](https://www.extensity.ai/) SymbolicAI contracts.

Every factual claim is *contractually required* to carry provenance.  
The final report cannot leave the system unless all validation contracts pass.

---

## Why this exists

ExtensityAI’s core thesis is that LLM outputs in research and enterprise settings must be **verifiable by construction**, not just post-hoc filtered. Their open-source SymbolicAI framework brings Design-by-Contract principles to generative models.

This project is a minimal, fully working demonstration of the same idea:

- Strict Pydantic contracts (`Claim` must have ≥1 `Source`, `VerifiedReport` must pass model validation)
- Explicit provenance / audit trail
- Free inference (Groq free tier – no credit card)
- One-click public deployment (Streamlit Community Cloud or Hugging Face Spaces)
- Zero ongoing cost

It is deliberately structured so the same logic can later be migrated to full SymbolicAI `@contract` + `Expression` classes.

---

## Quick start (local)

```bash
# 1. Clone / unzip
cd contracted-research-agent

# 2. Install
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Free API key (no credit card)
#    → https://console.groq.com
cp .env.example .env
# edit .env and paste your GROQ_API_KEY

# 4. Run
streamlit run app.py
```

Open http://localhost:8501

---

## Deploy live (zero cost)

### Option A – Streamlit Community Cloud (recommended)

1. Push this folder to a **public** GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) → Sign in with GitHub.
3. “New app” → select the repo → main file `app.py`.
4. Under **Advanced settings → Secrets** add:

```toml
GROQ_API_KEY = "gsk_your_key_here"
```

5. Deploy. You get a public URL like `https://yourname-contracted-research-agent.streamlit.app`.

### Option B – Hugging Face Spaces

1. Create a new Space (SDK = Streamlit, Hardware = CPU basic – free).
2. Upload the files (or connect the GitHub repo).
3. In Space settings → Variables and secrets → add `GROQ_API_KEY`.
4. The Space builds and gives you a public URL.

Both options are free forever for public apps.

---

## Architecture (contract flow)

```
ResearchQuestion  ──►  Plan  ──►  LLM generation (JSON)
                                      │
                                      ▼
                               Claim + Source objects
                                      │
                                      ▼
                          Pydantic model validation
                          (every claim must have ≥1 source)
                                      │
                                      ▼
                             VerifiedReport
                          (final contract gate)
                                      │
                                      ▼
                         Markdown + provenance + graph
```

Key files:

| File            | Role                                      |
|-----------------|-------------------------------------------|
| `contracts.py`  | All Design-by-Contract models             |
| `agent.py`      | Generation + validation pipeline          |
| `app.py`        | Streamlit UI + visualization              |
| `requirements.txt` | Minimal dependencies                   |

---

## Mapping to ExtensityAI / SymbolicAI

| This demo                        | SymbolicAI equivalent                     |
|----------------------------------|-------------------------------------------|
| Pydantic `BaseModel` + validators| `LLMDataModel` + `@contract` decorator   |
| Forced `sources: List[Source]`   | Pre/post conditions on expressions        |
| `VerifiedReport` final gate      | Contract success → typed return value     |
| ProvenanceTrace                  | Built-in tracing / metadata               |
| Free Groq backend                | `NEUROSYMBOLIC_ENGINE_MODEL = "groq:..."` |

Once you are comfortable with the contract pattern, the next natural step is to re-implement the same agent using SymbolicAI’s native `Expression` + `@contract` and their knowledge-graph / ontology tooling.

---

## License

MIT – free to use, modify, and share.  
If this helps you land a role or contributes to the neurosymbolic ecosystem, a star or a note is appreciated.

---

Built as an asymmetric signal: a working, inspectable, zero-cost system that embodies the principles ExtensityAI cares about.
