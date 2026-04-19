import streamlit as st
from datetime import date


def _dot_colour(value, low_thresh, high_thresh, low_is_bad=False) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "#888"
    if low_is_bad:
        if v >= high_thresh:
            return "#27ae60"
        if v <= low_thresh:
            return "#c0392b"
        return "#e67e22"
    else:
        if v >= high_thresh:
            return "#c0392b"
        if v <= low_thresh:
            return "#27ae60"
        return "#e67e22"


def _grade_colour(grade) -> str:
    try:
        g = int(grade)
    except (TypeError, ValueError):
        return "#888"
    if g >= 3:
        return "#c0392b"
    if g == 2:
        return "#e67e22"
    return "#27ae60"


def _stage_colour(stage: str) -> str:
    s = str(stage).upper()
    if s in ("IV", "IIIC", "IIIB"):
        return "#c0392b"
    if s in ("IIIA", "IIB"):
        return "#e67e22"
    return "#27ae60"


def _receptor_label(val) -> str:
    v = float(val) if val else 0.0
    if v >= 100:
        return f"POS ({v:.0f})"
    if v > 0:
        return f"LOW ({v:.0f})"
    return f"NEG ({v:.0f})"


def render_patient_card(features: dict):
    dob = features.get("date_of_birth")
    if dob:
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    else:
        age = None
    sex = features.get("biological_sex", "")

    diagnosis = features.get("histology") or features.get("cancer_type") or "—"
    stage = features.get("ajcc_stage") or "—"
    t = features.get("t_stage", "—")
    n = features.get("n_stage", "—")
    m = features.get("m_stage", "—")
    laterality = features.get("laterality", "—")
    actionable = features.get("actionable_mutations") or []
    actionable_str = ", ".join(actionable) if actionable else "None detected"

    dpyd_badge = ""
    if features.get("dpyd_variant"):
        dpyd_badge = (
            '<span style="background:#7a1a1a;color:#ffaaaa;padding:2px 8px;'
            'border-radius:4px;font-size:0.75em;font-weight:700;margin-left:10px">'
            '&#9888; DPYD VARIANT</span>'
        )

    age_str = f"{age}" if age is not None else "—"
    sex_str = sex.capitalize() if sex and sex != "unknown" else ""
    age_sex = f"{age_str} yrs" + (f" &middot; {sex_str}" if sex_str else "")

    # Patient profile header
    header_html = (
        '<div style="background:linear-gradient(135deg,#0a1929 0%,#0d2137 100%);'
        'border:1px solid #1e3a4f;border-left:4px solid #17a589;border-radius:10px;'
        'padding:18px 24px;margin-bottom:16px">'
        '<div style="display:flex;align-items:flex-start;gap:18px;flex-wrap:wrap">'

        # Person icon
        '<div style="width:52px;height:52px;border-radius:50%;background:#1e3a4f;'
        'border:2px solid #17a589;display:flex;align-items:center;justify-content:center;'
        'flex-shrink:0;font-size:1.6em">&#128100;</div>'

        # Fields
        '<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;flex:1">'

        '<div>'
        '<div style="font-size:0.68em;font-weight:700;letter-spacing:0.12em;color:#4a9aba;text-transform:uppercase;margin-bottom:4px">Patient ID</div>'
        f'<div style="font-size:1.35em;font-weight:800;color:#e8f4f8;letter-spacing:0.04em">{features["mrn"]}{dpyd_badge}</div>'
        f'<div style="font-size:0.85em;color:#7fb3c8;margin-top:2px">{age_sex}</div>'
        '</div>'

        '<div style="flex:1;min-width:180px">'
        '<div style="font-size:0.68em;font-weight:700;letter-spacing:0.12em;color:#4a9aba;text-transform:uppercase;margin-bottom:4px">Diagnosis</div>'
        f'<div style="font-size:0.9em;font-weight:600;color:#cde8f5">{diagnosis}</div>'
        '</div>'

        '<div>'
        '<div style="font-size:0.68em;font-weight:700;letter-spacing:0.12em;color:#4a9aba;text-transform:uppercase;margin-bottom:4px">Staging</div>'
        f'<div style="font-size:0.9em;font-weight:600;color:#cde8f5">T{t} N{n} M{m} &middot; {laterality}</div>'
        '</div>'

        '<div>'
        '<div style="font-size:0.68em;font-weight:700;letter-spacing:0.12em;color:#4a9aba;text-transform:uppercase;margin-bottom:4px">Actionable Mutations</div>'
        f'<div style="font-size:0.9em;font-weight:600;color:{"#f0b429" if actionable else "#6b8a9e"}">{actionable_str}</div>'
        '</div>'

        '</div></div></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # 5 metric cards — inject CSS then use st.columns + st.metric
    st.markdown("""
<style>
[data-testid="metric-container"] {
    background: #0d1f2d;
    border: 1px solid #1e3a4f;
    border-radius: 8px;
    padding: 14px 16px;
}
[data-testid="metric-container"] label {
    color: #4a9aba !important;
    font-size: 0.72em !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e8f4f8 !important;
    font-size: 1.6em !important;
    font-weight: 800 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

    grade_val = features.get("grade") or 0
    ki67_val = features.get("ki67_index") or 0.0
    tmb_val = features.get("tmb_score") or 0.0
    pdl1_val = features.get("pdl1_tps") or 0.0

    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        colour = _stage_colour(stage)
        st.markdown(
            f'<div style="border-top:3px solid {colour};border-radius:8px 8px 0 0;height:3px;margin-bottom:-3px"></div>',
            unsafe_allow_html=True,
        )
        st.metric("AJCC Stage", stage)

    with c2:
        colour = _grade_colour(grade_val)
        st.markdown(
            f'<div style="border-top:3px solid {colour};border-radius:8px 8px 0 0;height:3px;margin-bottom:-3px"></div>',
            unsafe_allow_html=True,
        )
        st.metric("Grade", str(grade_val) if grade_val else "—")

    with c3:
        colour = _dot_colour(ki67_val, 20, 30)
        st.markdown(
            f'<div style="border-top:3px solid {colour};border-radius:8px 8px 0 0;height:3px;margin-bottom:-3px"></div>',
            unsafe_allow_html=True,
        )
        st.metric("Ki-67", f"{ki67_val:.1f}%" if ki67_val else "—")
        st.caption("≥20% high · ≥30% aggressive")

    with c4:
        colour = _dot_colour(tmb_val, 6, 10, low_is_bad=True)
        st.markdown(
            f'<div style="border-top:3px solid {colour};border-radius:8px 8px 0 0;height:3px;margin-bottom:-3px"></div>',
            unsafe_allow_html=True,
        )
        st.metric("TMB", f"{tmb_val:.1f}" if tmb_val else "—")
        st.caption("mut/Mb · ≥10 high")

    with c5:
        colour = _dot_colour(pdl1_val, 1, 50, low_is_bad=True)
        st.markdown(
            f'<div style="border-top:3px solid {colour};border-radius:8px 8px 0 0;height:3px;margin-bottom:-3px"></div>',
            unsafe_allow_html=True,
        )
        st.metric("PD-L1 TPS", f"{pdl1_val:.0f}" if pdl1_val else "—")
        st.caption("% · ≥50 strong expr.")

    st.markdown("")

    # Patient Characteristics card — two-column split, no expanders
    er = features.get("er_hscore", 0)
    pr = features.get("pr_hscore", 0)
    her2 = features.get("her2_hscore", 0)

    TD_LABEL = 'padding:10px 20px 10px 8px;color:#7fb3c8;font-size:0.88em;white-space:nowrap;border-bottom:1px solid #1e3a4f;vertical-align:middle'
    TD_VALUE = 'padding:10px 8px 10px 20px;font-size:0.88em;font-weight:600;border-bottom:1px solid #1e3a4f;vertical-align:middle'

    def _row(label, value, colour="#cde8f5"):
        return (
            f'<tr>'
            f'<td style="{TD_LABEL}">{label}</td>'
            f'<td style="{TD_VALUE};color:{colour}">{value}</td>'
            f'</tr>'
        )

    def _receptor_colour(val):
        v = float(val) if val else 0.0
        if v >= 100:
            return "#27ae60"   # green — positive, targetable
        if v > 0:
            return "#e67e22"   # amber — low expression
        return "#c0392b"       # red — negative

    def _brca_colour(status):
        s = str(status).lower()
        if "pathogenic" in s or "mutated" in s or "variant" in s:
            return "#e67e22"   # amber — PARP inhibitor eligible
        return "#cde8f5"

    def _mmr_colour(status):
        return "#e67e22" if str(status).lower() in ("dmmr", "deficient") else "#cde8f5"

    def _mrd_colour(status):
        return "#c0392b" if str(status).lower() == "positive" else "#27ae60"

    def _egfr_colour(val):
        try:
            v = float(val)
            if v < 30:
                return "#c0392b"
            if v < 60:
                return "#e67e22"
            return "#27ae60"
        except (TypeError, ValueError):
            return "#cde8f5"

    def _lvef_colour(val):
        try:
            v = float(val)
            return "#c0392b" if v < 50 else "#cde8f5"
        except (TypeError, ValueError):
            return "#cde8f5"

    def _qtc_colour(val):
        try:
            v = float(val)
            return "#c0392b" if v > 470 else "#cde8f5"
        except (TypeError, ValueError):
            return "#cde8f5"

    ki67_val = features.get("ki67_index") or 0.0
    ki67_label = f"{ki67_val:.1f}%" if ki67_val else "—"
    ki67_colour = "#c0392b" if ki67_val >= 30 else ("#e67e22" if ki67_val >= 10 else "#27ae60")

    mol_rows = "".join([
        _row("Histology", features.get("histology", "—")),
        _row("ER (ESR1)", _receptor_label(er), _receptor_colour(er)),
        _row("PR (PGR)", _receptor_label(pr), _receptor_colour(pr)),
        _row("HER2 (ERBB2)", _receptor_label(her2), _receptor_colour(her2)),
        _row("Ki-67 index", ki67_label, ki67_colour),
        _row("BRCA1", features.get("brca1_status", "—"), _brca_colour(features.get("brca1_status", ""))),
        _row("BRCA2", features.get("brca2_status", "—"), _brca_colour(features.get("brca2_status", ""))),
        _row("MMR status", features.get("mmr_status", "—"), _mmr_colour(features.get("mmr_status", ""))),
        _row("HRD score", features.get("hrd_score", "—")),
        _row("POLE mutation", "Yes &#9888;" if features.get("pole_mutation") else "No",
             "#e67e22" if features.get("pole_mutation") else "#cde8f5"),
        _row("Actionable mutations",
             ", ".join(actionable) if actionable else "None",
             "#f0b429" if actionable else "#6b8a9e"),
    ])

    phys_rows = "".join([
        _row("eGFR", f"{features.get('egfr', '—')} ml/min", _egfr_colour(features.get("egfr"))),
        _row("LVEF", f"{features.get('lvef', '—')}%", _lvef_colour(features.get("lvef"))),
        _row("QTc", f"{features.get('qtc', '—')} ms", _qtc_colour(features.get("qtc"))),
        _row("CYP3A4", features.get("cyp3a4", "—")),
        _row("CYP2D6", features.get("cyp2d6", "—")),
        _row("DPYD variant",
             "Yes &#9888;" if features.get("dpyd_variant") else "No",
             "#c0392b" if features.get("dpyd_variant") else "#cde8f5"),
        _row("TPMT activity", features.get("tpmt_activity", "—")),
        _row("BMI", features.get("bmi", "—")),
        _row("Skeletal muscle index", features.get("smi", "—")),
        _row("ctDNA fraction", features.get("ctdna_fraction", "—")),
        _row("MRD status", features.get("mrd_status", "—"), _mrd_colour(features.get("mrd_status", ""))),
    ])

    section_label = (
        'font-size:0.72em;font-weight:700;letter-spacing:0.12em;'
        'color:#4a9aba;text-transform:uppercase;margin-bottom:12px;display:block'
    )

    characteristics_html = (
        '<div style="background:#0a1929;border:1px solid #1e3a4f;border-radius:10px;'
        'margin-top:8px;overflow:hidden">'

        '<div style="background:#0d2137;padding:12px 24px;border-bottom:1px solid #1e3a4f">'
        f'<span style="{section_label}">Patient Characteristics</span>'
        '</div>'

        '<div style="display:flex">'

        '<div style="flex:1;padding:24px 36px;border-right:1px solid #1e3a4f">'
        f'<span style="{section_label}">Molecular Profile</span>'
        f'<table style="width:100%;border-collapse:collapse">{mol_rows}</table>'
        '</div>'

        '<div style="flex:1;padding:24px 36px">'
        f'<span style="{section_label}">Patient Physiology</span>'
        f'<table style="width:100%;border-collapse:collapse">{phys_rows}</table>'
        '</div>'

        '</div></div>'
    )
    st.markdown(characteristics_html, unsafe_allow_html=True)
