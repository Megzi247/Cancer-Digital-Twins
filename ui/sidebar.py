import os
import streamlit as st
from db.queries import get_patient_list
from simulation.simulator import MODELS


def _env_key(name: str) -> str:
    """Return key from env/secrets if set, else empty string."""
    try:
        val = st.secrets.get(name, os.getenv(name, ""))
    except Exception:
        val = os.getenv(name, "")
    return val or ""


def render_sidebar() -> dict:
    st.sidebar.title("Cancer Digital Twin")
    st.sidebar.caption("Personalised drug response simulation · 100 synthetic breast cancer patients")

    st.sidebar.divider()

    # Patient selector
    patients = get_patient_list()
    patient_options = {mrn: str(pid) for mrn, pid in patients}
    selected_mrn = st.sidebar.selectbox("Patient", options=list(patient_options.keys()))
    selected_patient_id = patient_options[selected_mrn]

    st.sidebar.divider()

    # Drug selector
    all_drugs = [
        "ado-trastuzumab emtansine", "capecitabine", "cyclophosphamide",
        "doxorubicin", "letrozole", "olaparib", "paclitaxel",
        "palbociclib", "pembrolizumab", "pertuzumab", "tamoxifen", "trastuzumab",
    ]
    selected_drugs = st.sidebar.multiselect(
        "Drug combination",
        options=all_drugs,
        placeholder="Select one or more drugs",
    )

    # Treatment intent
    treatment_intent = st.sidebar.selectbox(
        "Treatment intent",
        options=["adjuvant", "neoadjuvant", "palliative"],
    )

    # Model selector
    st.sidebar.divider()
    model_label = st.sidebar.radio(
        "AI model",
        options=list(MODELS.keys()),
        index=0,
    )

    # API keys — pre-filled from env/secrets if available, otherwise user must enter
    st.sidebar.divider()
    with st.sidebar.expander("🔑 API keys", expanded=False):
        anthropic_key = st.text_input(
            "Anthropic API key",
            value=_env_key("ANTHROPIC_API_KEY"),
            type="password",
            placeholder="sk-ant-...",
            help="Required for Claude (Anthropic)",
        )
        openai_key = st.text_input(
            "OpenAI API key",
            value=_env_key("OPENAI_API_KEY"),
            type="password",
            placeholder="sk-proj-...",
            help="Required for GPT-4o (OpenAI)",
        )

    st.sidebar.divider()

    run = st.sidebar.button("Run Simulation", type="primary", use_container_width=True)
    st.sidebar.caption("ClickHouse + aisuite · Synthetic data only")

    return {
        "mrn": selected_mrn,
        "patient_id": selected_patient_id,
        "drugs": selected_drugs,
        "treatment_intent": treatment_intent,
        "model_label": model_label,
        "anthropic_key": anthropic_key,
        "openai_key": openai_key,
        "run": run,
    }
