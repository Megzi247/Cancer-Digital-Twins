import streamlit as st

DARK_BG = "#f8fafc"
CARD_BG = "#ffffff"
HEADER_BG = "#f1f5f9"
BORDER = "#e2e8f0"
LABEL_COL = "#0068c9"
TEXT_COL = "#1e293b"
DIM_COL = "#64748b"

SECTION_LABEL = (
    "font-size:0.72em;font-weight:700;letter-spacing:0.12em;"
    f"color:{LABEL_COL};text-transform:uppercase;display:block;margin-bottom:10px"
)

LEVEL_COLOURS = {
    "low":        ("#16a34a", "#f0fdf4"),
    "moderate":   ("#d97706", "#fffbeb"),
    "medium":     ("#d97706", "#fffbeb"),
    "high":       ("#dc2626", "#fef2f2"),
    "good":       ("#16a34a", "#f0fdf4"),
    "acceptable": ("#d97706", "#fffbeb"),
    "poor":       ("#dc2626", "#fef2f2"),
    "cr":         ("#16a34a", "#f0fdf4"),
    "pr":         ("#16a34a", "#f0fdf4"),
    "sd":         ("#d97706", "#fffbeb"),
    "pd":         ("#dc2626", "#fef2f2"),
}


def _level_colour(level: str):
    return LEVEL_COLOURS.get(str(level).lower(), ("#64748b", "#f8fafc"))


def _pill(label: str, level: str) -> str:
    fg, bg = _level_colour(level)
    return (
        f'<span style="background:{bg};color:{fg};border:1px solid {fg};'
        f'padding:2px 10px;border-radius:12px;font-weight:700;font-size:1.0em">'
        f'{label}</span>'
    )


def _row(label, value, colour=TEXT_COL):
    return (
        f'<tr>'
        f'<td style="padding:10px 20px 10px 8px;color:{DIM_COL};font-size:0.96em;'
        f'white-space:nowrap;border-bottom:1px solid {BORDER};vertical-align:middle">{label}</td>'
        f'<td style="padding:10px 8px 10px 20px;color:{colour};font-size:0.96em;'
        f'font-weight:600;border-bottom:1px solid {BORDER};vertical-align:middle">{value}</td>'
        f'</tr>'
    )


def _card_html(header: str, body_html: str, accent: str = "#17a589") -> str:
    return (
        f'<div style="background:{CARD_BG};border:1px solid {BORDER};'
        f'border-top:3px solid {accent};border-radius:10px;overflow:hidden;height:100%">'
        f'<div style="background:{HEADER_BG};padding:12px 24px;border-bottom:1px solid {BORDER}">'
        f'<span style="{SECTION_LABEL}">{header}</span>'
        f'</div>'
        f'<div style="padding:20px 28px">{body_html}</div>'
        f'</div>'
    )


def render_ddi_error(message: str):
    st.markdown(
        f'<div style="background:#fef2f2;border:1px solid #dc2626;border-left:5px solid #dc2626;'
        f'border-radius:8px;padding:18px 24px;margin-bottom:12px">'
        f'<div style="font-size:0.72em;font-weight:700;letter-spacing:0.12em;color:#dc2626;'
        f'text-transform:uppercase;margin-bottom:6px">&#9888; Drug Interaction — Simulation Blocked</div>'
        f'<div style="color:#991b1b;font-size:0.95em">{message}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_results(result: dict, model_label: str):
    if "parse_error" in result:
        st.warning("Simulation returned an unexpected format.")
        with st.expander("Raw model response"):
            st.text(result.get("raw_response", ""))
        return

    context   = result.get("clinical_context", {})
    efficacy  = result.get("efficacy", {})
    toxicity  = result.get("toxicity", {})
    resistance = result.get("resistance", {})

    fit       = context.get("regimen_fit", "")
    subtype   = context.get("molecular_subtype", "")
    guideline = context.get("guideline_alignment", "")
    rationale = context.get("fit_rationale", "")

    fit_fg, fit_bg = _level_colour(fit)

    # Clinical context header card
    st.markdown(
        f'<div style="background:{fit_bg};border:1px solid {fit_fg};border-left:5px solid {fit_fg};'
        f'border-radius:8px;padding:16px 24px;margin-bottom:16px">'
        f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">'
        f'<span style="font-size:1.1em;font-weight:800;color:{fit_fg}">{subtype}</span>'
        f'{_pill(fit.upper(), fit)}'
        f'<span style="font-size:1.0em;color:{DIM_COL}">{guideline}</span>'
        f'</div>'
        f'<div style="font-size:0.96em;color:{TEXT_COL};margin-top:6px">{rationale}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── EFFICACY ──────────────────────────────────────────────
    prob   = efficacy.get("response_probability", 0)
    recist = efficacy.get("predicted_recist", "—")
    conf   = efficacy.get("confidence", "")
    pfs    = efficacy.get("pfs_estimate_months", "—")
    prob_fg, _ = _level_colour("low" if prob >= 0.6 else ("medium" if prob >= 0.3 else "high"))
    bar_filled = int(float(prob) * 100)

    drivers = efficacy.get("key_drivers", [])

    def _driver_detail(d):
        if isinstance(d, dict):
            return f'<span style="color:{DIM_COL}"> · {d.get("value","")} — {d.get("impact","")}</span>'
        return ""

    def _driver_name(d):
        return d.get("biomarker", "—") if isinstance(d, dict) else d

    driver_items = "".join(
        f'<div style="background:#fefce8;border-left:3px solid #d97706;padding:6px 12px;'
        f'border-radius:4px;margin:4px 0;font-size:0.94em">'
        f'<span style="color:#b45309;font-weight:700">{_driver_name(d)}</span>'
        f'{_driver_detail(d)}'
        f'</div>'
        for d in drivers
    )
    reasoning = efficacy.get("reasoning", "")
    reasoning_html = (
        f'<div style="background:#f8fafc;border-left:3px solid {BORDER};padding:10px 14px;'
        f'border-radius:4px;font-size:1.0em;color:{DIM_COL};line-height:1.55">{reasoning}</div>'
    ) if reasoning else ""

    efficacy_html = (
        f'<div style="display:flex;gap:0">'

        # Left stat panel
        f'<div style="min-width:200px;padding-right:28px;border-right:1px solid {BORDER}">'
        f'<div style="font-size:0.75em;color:{DIM_COL};margin-bottom:2px">RESPONSE PROBABILITY</div>'
        f'<div style="font-size:2.6em;font-weight:800;color:{prob_fg};line-height:1">{prob:.0%}</div>'
        f'<div style="background:#e2e8f0;border-radius:4px;height:6px;margin:8px 0 14px">'
        f'<div style="background:{prob_fg};width:{bar_filled}%;height:6px;border-radius:4px"></div></div>'
        f'<table style="border-collapse:collapse">'
        f'{_row("RECIST", _pill(recist, recist))}'
        f'{_row("PFS", pfs)}'
        f'{_row("Confidence", conf.capitalize())}'
        f'</table>'
        f'</div>'

        # Right detail panel
        f'<div style="flex:1;padding-left:28px">'
        f'<span style="{SECTION_LABEL}">Key Drivers</span>'
        f'{driver_items}'
        f'{reasoning_html}'
        f'</div>'

        f'</div>'
    )
    st.markdown(_card_html("Efficacy", efficacy_html, prob_fg), unsafe_allow_html=True)

    # ── TOXICITY ──────────────────────────────────────────────
    overall   = toxicity.get("overall_risk", "")
    top_risks = toxicity.get("top_risks", [])
    adj       = toxicity.get("dose_adjustment")
    monitor   = toxicity.get("monitoring_schedule", "—")
    overall_fg, _ = _level_colour(overall)

    def _risk_item(risk):
        grade = risk.get("ctcae_grade", "?")
        level = risk.get("risk_level", "")
        name  = risk.get("toxicity_name", risk.get("organ", "?"))
        drug  = risk.get("causative_drug", "")
        reason = risk.get("reason", "")
        return (
            f'<div style="display:flex;align-items:flex-start;gap:12px;padding:8px 0;border-bottom:1px solid {BORDER}">'
            f'{_pill(f"Gr {grade}", level)}'
            f'<div>'
            f'<div style="color:{TEXT_COL};font-size:0.96em;font-weight:600">{name}</div>'
            f'<div style="color:{DIM_COL};font-size:0.88em">{drug} · {reason}</div>'
            f'</div></div>'
        )

    risk_items = "".join(_risk_item(r) for r in top_risks)
    adj_html = (
        f'<div style="background:#fffbeb;border:1px solid #d97706;border-radius:6px;'
        f'padding:8px 14px;margin-top:10px;font-size:0.93em;color:#92400e">'
        f'&#9888; <strong>Dose adjustment:</strong> {adj}</div>'
    ) if adj else ""

    toxicity_html = (
        f'<div style="display:flex;gap:0">'

        f'<div style="min-width:200px;padding-right:28px;border-right:1px solid {BORDER}">'
        f'<div style="font-size:0.75em;color:{DIM_COL};margin-bottom:2px">OVERALL RISK</div>'
        f'<div style="font-size:2.6em;font-weight:800;color:{overall_fg};line-height:1">{overall.capitalize()}</div>'
        f'<div style="height:14px"></div>'
        f'<span style="{SECTION_LABEL}">Monitoring</span>'
        f'<div style="font-size:0.94em;color:{TEXT_COL};line-height:1.5">{monitor}</div>'
        f'</div>'

        f'<div style="flex:1;padding-left:28px">'
        f'<span style="{SECTION_LABEL}">Top Risks</span>'
        f'{risk_items}'
        f'{adj_html}'
        f'</div>'

        f'</div>'
    )
    st.markdown(_card_html("Toxicity", toxicity_html, overall_fg), unsafe_allow_html=True)

    # ── RESISTANCE ────────────────────────────────────────────
    tier      = resistance.get("risk_tier", "")
    ttr       = resistance.get("time_to_resistance_estimate", "—")
    primary   = resistance.get("primary_mechanism", "—")
    secondary = resistance.get("secondary_mechanism")
    cross     = resistance.get("cross_resistance_risk")
    mon       = resistance.get("monitoring", "—")
    salvage   = resistance.get("salvage_options", [])
    tier_fg, _ = _level_colour(tier)

    salvage_items = "".join(
        f'<div style="background:#eff6ff;border-left:3px solid {LABEL_COL};'
        f'padding:6px 12px;border-radius:4px;margin:4px 0;'
        f'font-size:0.93em;font-weight:600;color:{TEXT_COL}">&#128138; {s}</div>'
        for s in salvage
    )

    mech_rows = _row("Primary mechanism", primary)
    if secondary:
        mech_rows += _row("Secondary", secondary)
    if cross:
        mech_rows += _row("Cross-resistance", cross, "#e67e22")

    resistance_html = (
        f'<div style="display:flex;gap:0">'

        f'<div style="min-width:200px;padding-right:28px;border-right:1px solid {BORDER}">'
        f'<div style="font-size:0.75em;color:{DIM_COL};margin-bottom:2px">RISK TIER</div>'
        f'<div style="font-size:2.6em;font-weight:800;color:{tier_fg};line-height:1">{tier.capitalize()}</div>'
        f'<div style="height:14px"></div>'
        f'<table style="border-collapse:collapse">{_row("Time to resistance", ttr)}</table>'
        f'<div style="margin-top:14px">'
        f'<span style="{SECTION_LABEL}">Liquid Biopsy Monitor</span>'
        f'<div style="font-size:0.94em;color:{TEXT_COL};line-height:1.5">{mon}</div>'
        f'</div>'
        f'</div>'

        f'<div style="flex:1;padding-left:28px">'
        f'<span style="{SECTION_LABEL}">Resistance Mechanisms</span>'
        f'<table style="width:100%;border-collapse:collapse">{mech_rows}</table>'
        + (
            f'<div style="margin-top:16px">'
            f'<span style="{SECTION_LABEL}">If Resistance Develops</span>'
            f'{salvage_items}</div>'
            if salvage else ""
        ) +
        f'</div>'

        f'</div>'
    )
    st.markdown(_card_html("Resistance", resistance_html, tier_fg), unsafe_allow_html=True)

    # ── CLINICAL NARRATIVE ────────────────────────────────────
    narrative = result.get("narrative", "")
    if narrative:
        st.markdown(
            f'<div style="background:{CARD_BG};border:1px solid {BORDER};border-left:4px solid #17a589;'
            f'border-radius:8px;padding:18px 28px;margin-top:16px">'
            f'<span style="{SECTION_LABEL}">Clinical Summary</span>'
            f'<div style="font-size:1.0em;color:{TEXT_COL};line-height:1.65">{narrative}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Footer
    key_drivers = efficacy.get("key_drivers", [])
    if key_drivers:
        driver_names = [
            d.get("biomarker", "") if isinstance(d, dict) else d
            for d in key_drivers
        ]
        st.markdown(
            f'<div style="font-size:0.75em;color:{DIM_COL};margin-top:8px;text-align:right">'
            f'Key biomarkers: {" · ".join(driver_names)} &nbsp;·&nbsp; Model: {model_label}'
            f'</div>',
            unsafe_allow_html=True,
        )
