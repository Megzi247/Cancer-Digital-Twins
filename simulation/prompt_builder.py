def build_simulation_prompt(features: dict, drug_data: dict, treatment_intent: str) -> str:
    drugs = drug_data.get("drugs", [])
    synergy = drug_data.get("synergy", [])

    drug_lines = "\n".join(
        f"  - {d[1]} ({d[2]}): {d[3]}, target={d[4]}, pathway={d[5]}"
        for d in drugs
    )
    synergy_lines = "\n".join(
        f"  - synergy_score={s[2]}, antagonism={s[3]}" for s in synergy
    ) or "  - No synergy data"

    mutations = ", ".join(features["actionable_mutations"]) or "none"

    prompt = f"""You are a precision oncology simulation engine with expertise in breast cancer pharmacology. Given a patient's full molecular and clinical profile and a proposed drug regimen, produce a detailed, clinician-grade prediction across four domains: clinical context, efficacy, toxicity, and resistance.

Be specific. Always cite the patient's actual biomarker values in your reasoning (e.g. "ER H-score of 232 indicates strong endocrine sensitivity"). Avoid generic statements. Every claim must trace back to a field in the patient profile below.

## Patient Profile

MRN: {features['mrn']}
Tumour: {features['histology']}, {features['cancer_type']}
Stage: {features['ajcc_stage']} (T{features['t_stage']} N{features['n_stage']} M{features['m_stage']}), Grade {features['grade']}
Laterality: {features['laterality']}
Treatment intent: {treatment_intent}

### Receptor Status
ER (ESR1 H-score): {features['er_hscore']}
PR (PGR H-score): {features['pr_hscore']}
HER2 (ERBB2 H-score): {features['her2_hscore']}
Ki-67 index: {features['ki67_index']}%

### DNA Repair & Genomics
BRCA1: {features['brca1_status']}
BRCA2: {features['brca2_status']}
MMR status: {features['mmr_status']}
TMB score: {features['tmb_score']}
HRD score: {features['hrd_score']}
POLE mutation: {features['pole_mutation']}
Actionable mutations (OncoKB level 1/2): {mutations}

### Immune Microenvironment
CD8+ T cells: {features['cd8_pct']}%
M2 macrophages: {features['m2_pct']}%
Tregs: {features['treg_pct']}%
PD-L1 TPS: {features['pdl1_tps']}
PD-L1 CPS: {features['pdl1_cps']}
TGF-β: {features['tgf_beta']}
IFN-γ: {features['ifn_gamma']}

### Tumour Microenvironment
HIF-1α: {features['hif1a']}
O2 saturation: {features['o2_saturation']}%
Interstitial fluid pressure: {features['ifp']}
Tumour pH: {features['tumor_ph']}

### Organ Function
eGFR: {features['egfr']} ml/min
ALT: {features['alt']} U/L
Bilirubin: {features['bilirubin']} μmol/L
Albumin: {features['albumin']} g/L
LVEF: {features['lvef']}%
QTc: {features['qtc']} ms

### Pharmacogenomics
CYP2D6: {features['cyp2d6']}
CYP3A4: {features['cyp3a4']}
UGT1A1: {features['ugt1a1']}
DPYD variant: {features['dpyd_variant']}
TPMT activity: {features['tpmt_activity']}

### Body Composition & Other
BMI: {features['bmi']}
Skeletal muscle index: {features['smi']}
Akkermansia abundance: {features['akkermansia']}
Recent antibiotics: {features['antibiotic_recent']}
Estradiol: {features['estradiol']} pmol/L
ctDNA fraction: {features['ctdna_fraction']}
MRD status: {features['mrd_status']}
MDR1 expression: {features['mdr1_expression']}

## Proposed Regimen

{drug_lines}

### Combination Synergy
{synergy_lines}

## Instructions

Return ONLY a valid JSON object with this exact structure — no markdown, no explanation outside the JSON:

{{
  "clinical_context": {{
    "molecular_subtype": "<e.g. HR+/HER2-, TNBC, HER2+>",
    "subtype_rationale": "<1-2 sentences citing specific biomarker values that define this subtype>",
    "regimen_fit": "<good|acceptable|poor>",
    "guideline_alignment": "<e.g. NCCN Category 1, off-label, investigational>",
    "fit_rationale": "<1-2 sentences explaining why this regimen fits or does not fit this patient>"
  }},
  "efficacy": {{
    "response_probability": <float 0.0-1.0>,
    "pfs_estimate_months": "<range e.g. 18-24 months>",
    "pcr_probability": <float 0.0-1.0 or null if not neoadjuvant>,
    "predicted_recist": "<CR|PR|SD|PD>",
    "confidence": "<low|medium|high>",
    "key_drivers": [
      {{"biomarker": "<name>", "value": "<patient value>", "impact": "<how it influences response>"}}
    ],
    "reasoning": "<3-4 sentences citing actual patient biomarker values>"
  }},
  "toxicity": {{
    "overall_risk": "<low|moderate|high>",
    "top_risks": [
      {{
        "organ": "<organ>",
        "toxicity_name": "<specific toxicity e.g. febrile neutropenia>",
        "ctcae_grade": "<expected grade 1-4>",
        "causative_drug": "<which drug in regimen drives this>",
        "risk_level": "<low|moderate|high>",
        "reason": "<cite patient-specific factor driving this risk>"
      }}
    ],
    "dose_adjustment": "<specific recommendation with percentage reduction if applicable, or null>",
    "monitoring_schedule": "<recommended CBC, LFT, or other monitoring frequency>"
  }},
  "resistance": {{
    "risk_tier": "<low|medium|high>",
    "time_to_resistance_estimate": "<range in months>",
    "primary_mechanism": "<most likely resistance mechanism with molecular basis>",
    "secondary_mechanism": "<second most likely mechanism or null>",
    "cross_resistance_risk": "<drugs or classes that may be compromised if resistance develops>",
    "monitoring": "<specific ctDNA or liquid biopsy markers to watch>",
    "salvage_options": ["<recommended next-line regimen 1>", "<recommended next-line regimen 2>"]
  }},
  "ddi_flag": null
}}"""
    return prompt


def build_narrative_prompt(simulation_result: dict, features: dict, drug_names: list[str]) -> str:
    efficacy = simulation_result.get("efficacy", {})
    toxicity = simulation_result.get("toxicity", {})
    resistance = simulation_result.get("resistance", {})
    context = simulation_result.get("clinical_context", {})

    key_drivers = efficacy.get("key_drivers", [])
    if key_drivers and isinstance(key_drivers[0], dict):
        driver_text = "; ".join(
            f"{d['biomarker']} ({d['value']}): {d['impact']}" for d in key_drivers
        )
    else:
        driver_text = ", ".join(key_drivers)

    top_risks = toxicity.get("top_risks", [])
    risk_text = "; ".join(
        f"{r.get('toxicity_name','?')} grade {r.get('ctcae_grade','?')} ({r.get('causative_drug','?')})"
        for r in top_risks
    )

    return f"""You are a senior clinical oncologist presenting at a multidisciplinary tumour board. Write a concise, authoritative 4-5 sentence clinical summary of the simulation findings below.

Rules:
- Cite specific biomarker values and patient data — do not speak in generalities
- Lead with the bottom line (is this regimen appropriate for this patient?)
- Include the most important toxicity concern and what to monitor
- End with the resistance outlook and what to do if treatment fails
- Use clinical language suitable for an oncologist audience

Patient: {features['mrn']}, {features['histology']}, Stage {features['ajcc_stage']}, {context.get('molecular_subtype', '')}
Regimen: {', '.join(drug_names)}
Guideline alignment: {context.get('guideline_alignment', '')}

Efficacy: {efficacy.get('response_probability', '')} response probability, predicted {efficacy.get('predicted_recist', '')}, PFS estimate {efficacy.get('pfs_estimate_months', '')}, confidence {efficacy.get('confidence', '')}
Key drivers: {driver_text}
Toxicity: {toxicity.get('overall_risk', '')} overall risk — {risk_text}
Dose adjustment: {toxicity.get('dose_adjustment', 'none')}
Monitoring: {toxicity.get('monitoring_schedule', '')}
Resistance: {resistance.get('risk_tier', '')} risk, {resistance.get('time_to_resistance_estimate', '')}, primary mechanism: {resistance.get('primary_mechanism', '')}
Salvage options: {', '.join(resistance.get('salvage_options', []))}

Write the tumour board summary now:"""
