"""
Contracted Research Agent – Streamlit frontend
Zero-cost demo of Design-by-Contract research automation.
Inspired by ExtensityAI SymbolicAI principles.
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Contracted Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Sidebar – configuration & philosophy
# --------------------------------------------------------------------------
with st.sidebar:
    st.title("🔬 Contracted Research Agent")
    st.markdown(
        """
        **Design-by-Contract** research automation.

        Every claim is forced to carry provenance.
        The final report cannot be returned unless all contracts pass.
        """
    )
    st.divider()
    st.subheader("Engine")
    model = st.selectbox(
        "Groq model (free tier)",
        [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen/qwen3-32b",
            "moonshotai/kimi-k2-instruct",
        ],
        index=0,
        help="All of these are available on Groq free tier (no credit card).",
    )
    st.caption("Get a free key → [console.groq.com](https://console.groq.com)")
    st.divider()
    st.markdown(
        """
        ### Why this matters
        ExtensityAI’s SymbolicAI brings Design-by-Contract
        to LLMs so that outputs are verifiable *by construction*.

        This demo shows the same idea with pure Pydantic contracts
        + free inference so anyone can run and inspect it.
        """
    )
    st.markdown("---")
    st.caption("Built as an asymmetric signal for ExtensityAI · Zero ongoing cost")

# --------------------------------------------------------------------------
# Main UI
# --------------------------------------------------------------------------
st.title("Verifiable Research Agent")
st.markdown(
    "Ask a research question. The agent will produce a structured report "
    "where **every claim is contractually required to have sources**."
)

col1, col2 = st.columns([2, 1])
with col1:
    question = st.text_area(
        "Research question",
        height=100,
        placeholder="e.g. What are the most evidence-based non-pharmacological interventions for chronic tinnitus in adults?",
    )
with col2:
    domain = st.text_input("Domain (optional)", placeholder="neuroscience / audiology")
    constraints = st.text_area(
        "Constraints (optional)",
        height=68,
        placeholder="only peer-reviewed 2018+, prefer systematic reviews & RCTs, max 8 claims",
    )

run = st.button("Generate verified report", type="primary", use_container_width=True)

if run:
    if not question or len(question.strip()) < 10:
        st.error("Please enter a research question (at least 10 characters).")
        st.stop()

    if not os.getenv("GROQ_API_KEY"):
        st.error(
            "GROQ_API_KEY is missing. "
            "Add it in Streamlit secrets or a local .env file. "
            "Free key: https://console.groq.com"
        )
        st.stop()

    with st.status("Running contracted research pipeline…", expanded=True) as status:
        st.write("1. Accepting input under ResearchQuestion contract")
        try:
            from agent import generate_verified_report

            report, steps = generate_verified_report(
                question=question.strip(),
                domain=domain.strip() or None,
                constraints=constraints.strip() or None,
                model=model,
            )
            for step in steps:
                st.write(f"• {step}")
            status.update(label="All contracts passed ✓", state="complete")
        except Exception as e:
            status.update(label="Contract or generation failure", state="error")
            st.exception(e)
            st.stop()

    # Results
    st.success("VerifiedReport contract satisfied — every claim has provenance.")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📄 Report", "🔗 Provenance", "📊 Claims graph", "⬇️ Export"]
    )

    with tab1:
        st.markdown(report.to_markdown())

    with tab2:
        st.subheader("Audit trail")
        st.json(
            {
                "question": report.provenance.question,
                "model": report.provenance.model_used,
                "timestamp": report.provenance.timestamp,
                "contract_checks_passed": report.provenance.contract_checks_passed,
                "steps": report.provenance.steps,
            }
        )
        st.subheader("Limitations (declared by agent)")
        st.info(report.limitations)

    with tab3:
        # Simple claim–source network
        try:
            import networkx as nx
            import plotly.graph_objects as go

            G = nx.Graph()
            for i, claim in enumerate(report.all_claims):
                cnode = f"C{i+1}"
                G.add_node(cnode, label=claim.text[:60] + "…", type="claim")
                for j, src in enumerate(claim.sources):
                    snode = f"S{i+1}-{j+1}"
                    G.add_node(snode, label=src.title[:40], type="source")
                    G.add_edge(cnode, snode)

            pos = nx.spring_layout(G, seed=42)
            edge_x, edge_y = [], []
            for e in G.edges():
                x0, y0 = pos[e[0]]
                x1, y1 = pos[e[1]]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]

            node_x, node_y, node_text, node_color = [], [], [], []
            for n in G.nodes():
                x, y = pos[n]
                node_x.append(x)
                node_y.append(y)
                node_text.append(G.nodes[n]["label"])
                node_color.append("#1f77b4" if G.nodes[n]["type"] == "claim" else "#2ca02c")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1, color="#888"), hoverinfo="none"))
            fig.add_trace(
                go.Scatter(
                    x=node_x,
                    y=node_y,
                    mode="markers+text",
                    text=[n for n in G.nodes()],
                    textposition="top center",
                    marker=dict(size=18, color=node_color),
                    hovertext=node_text,
                    hoverinfo="text",
                )
            )
            fig.update_layout(
                title="Claim ↔ Source graph (blue = claim, green = source)",
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20),
                height=500,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Graph visualization skipped: {e}")

    with tab4:
        md = report.to_markdown()
        st.download_button(
            "Download Markdown report",
            data=md,
            file_name="verified_research_report.md",
            mime="text/markdown",
        )
        st.code(md, language="markdown")

# Footer
st.divider()
st.caption(
    "This project demonstrates Design-by-Contract principles for LLM research agents. "
    "It is intentionally simple, fully open, and runs at zero cost on Groq free tier + Streamlit Community Cloud. "
    "Architecture is deliberately compatible with migration to ExtensityAI SymbolicAI contracts."
)
