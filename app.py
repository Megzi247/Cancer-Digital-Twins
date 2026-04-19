import base64
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

st.set_page_config(
    page_title="Cancer Digital Twin",
    page_icon="🧬",
    layout="wide",
)

from db.queries import get_drug_ids, get_drug_data
from simulation.feature_builder import build_patient_features
from simulation.ddi_checker import run_ddi_check
from simulation.simulator import run_simulation
from ui.sidebar import render_sidebar
from ui.patient_card import render_patient_card
from ui.results_panel import render_results, render_ddi_error


def _image_b64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


def _render_background():
    img_path = Path(__file__).parent / "image_background.png"
    if not img_path.exists():
        return
    b64 = _image_b64(str(img_path))
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(5, 15, 30, 0.78);
            z-index: 0;
            pointer-events: none;
        }}
        section[data-testid="stSidebar"] {{
            z-index: 100;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_session():
    if "history" not in st.session_state:
        st.session_state.history = []


def _save_to_history(mrn, drugs, intent, model_label, result):
    st.session_state.history.insert(0, {
        "mrn": mrn, "drugs": drugs, "intent": intent,
        "model": model_label, "result": result,
    })
    st.session_state.history = st.session_state.history[:10]


def _render_history():
    if not st.session_state.history:
        return
    with st.sidebar.expander(f"Previous runs ({len(st.session_state.history)})"):
        for i, run in enumerate(st.session_state.history):
            efficacy = run["result"].get("efficacy", {})
            prob = efficacy.get("response_probability", 0)
            recist = efficacy.get("predicted_recist", "?")
            label = f"{run['mrn']} · {', '.join(run['drugs'])} · {prob:.0%} {recist}"
            if st.button(label, key=f"history_{i}", use_container_width=True):
                st.session_state.selected_history = i


def main():
    _init_session()
    _render_background()

    sidebar = render_sidebar()
    mrn = sidebar["mrn"]
    patient_id = sidebar["patient_id"]
    drug_names = sidebar["drugs"]
    treatment_intent = sidebar["treatment_intent"]
    model_label = sidebar["model_label"]
    anthropic_key = sidebar["anthropic_key"]
    openai_key = sidebar["openai_key"]
    run = sidebar["run"]

    _render_history()

    # Load patient features
    try:
        features = build_patient_features(patient_id, mrn)
    except Exception as e:
        st.error("Database connection failed. Check ClickHouse is running on port 9000.")
        print(f"[DB ERROR] {e}")
        return

    if not features.get("has_molecular_data"):
        st.warning("No genomic sample found for this patient. Proceeding with clinical features only.")

    render_patient_card(features)

    # History replay
    if "selected_history" in st.session_state:
        idx = st.session_state.selected_history
        if idx < len(st.session_state.history):
            past = st.session_state.history[idx]
            st.markdown(
                f"*Showing previous run: {past['mrn']} · "
                f"{', '.join(past['drugs'])} · {past['intent']} · {past['model']}*"
            )
            render_results(past["result"], past["model"])
            if st.button("Clear / run new simulation"):
                del st.session_state.selected_history
                st.rerun()
            return

    if not run:
        st.markdown("---")
        st.markdown("Select drugs in the sidebar and click **Run Simulation**.")
        return

    if not drug_names:
        st.warning("Please select at least one drug.")
        return

    needs_anthropic = "Anthropic" in model_label
    needs_openai = "OpenAI" in model_label
    if needs_anthropic and not anthropic_key:
        st.error("An Anthropic API key is required to use Claude. Enter it in the **API keys** section of the sidebar.")
        return
    if needs_openai and not openai_key:
        st.error("An OpenAI API key is required to use GPT-4o. Enter it in the **API keys** section of the sidebar.")
        return

    result = None
    with st.status("Running simulation…", expanded=True) as status:
        try:
            st.write("🔍 Resolving drug data…")
            drug_map = get_drug_ids(drug_names)
            missing = [d for d in drug_names if d not in drug_map]
            if missing:
                status.update(label="Unknown drugs", state="error")
                st.error(f"Unknown drugs: {', '.join(missing)}")
                return
            drug_ids = list(drug_map.values())
            drug_data = get_drug_data(drug_ids)

            st.write("⚠️ Checking drug-drug interactions…")
            blocked, ddi_message = run_ddi_check(drug_ids)
            if blocked:
                status.update(label="Simulation blocked — drug interaction detected", state="error")
                render_ddi_error(ddi_message)
                return

            st.write("🧬 Building patient feature vector…")

            st.write(f"🤖 Calling {model_label} — generating predictions…")
            result = run_simulation(
                features, drug_data, drug_names, treatment_intent,
                model_label=model_label,
                anthropic_key=anthropic_key,
                openai_key=openai_key,
            )

            st.write("✍️ Generating clinical narrative…")
            status.update(label="Simulation complete", state="complete", expanded=False)

        except Exception as e:
            status.update(label="Simulation failed", state="error")
            st.error(f"Simulation failed: {e}")
            print(f"[SIM ERROR] {type(e).__name__}: {e}")
            return

    if result:
        _save_to_history(mrn, drug_names, treatment_intent, model_label, result)
        render_results(result, model_label)


if __name__ == "__main__":
    main()
