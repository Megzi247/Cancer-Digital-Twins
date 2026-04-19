from db.queries import get_genomic_sample, get_patient_features


def build_patient_features(patient_id: str, mrn: str) -> dict:
    sample = get_genomic_sample(patient_id)
    has_molecular = sample is not None
    sample_id = str(sample[0]) if sample else None

    raw = get_patient_features(patient_id, sample_id) if sample_id else {}

    def f(val, default=0.0, decimals=2):
        return round(float(val), decimals) if val is not None else default

    def s(val, default="unknown"):
        return str(val) if val is not None else default

    def b(val):
        return bool(val) if val is not None else False

    demo = raw.get("demographics") or []
    staging = raw.get("staging") or []
    proteins = raw.get("proteins") or {}
    cc = raw.get("cell_cycle") or []
    dna = raw.get("dna_repair") or []
    immune = raw.get("immune") or []
    chk = raw.get("checkpoint") or []
    cyt = raw.get("cytokine") or []
    hyp = raw.get("hypoxia") or []
    org = raw.get("organ") or []
    pgx = raw.get("pgx") or []
    body = raw.get("body") or []
    micro = raw.get("microbiome") or []
    horm = raw.get("hormonal") or []
    biopsy = raw.get("biopsy") or []
    resist = raw.get("resistance") or []

    return {
        "mrn": mrn,
        "has_molecular_data": has_molecular,
        "date_of_birth": demo[0] if demo else None,
        "biological_sex": s(demo[1] if demo else None),

        # Tumor staging
        "cancer_type": s(staging[0] if staging else None),
        "histology": s(staging[1] if staging else None),
        "t_stage": s(staging[2] if staging else None),
        "n_stage": s(staging[3] if staging else None),
        "m_stage": s(staging[4] if staging else None),
        "ajcc_stage": s(staging[5] if staging else None),
        "grade": int(staging[6]) if staging and staging[6] is not None else 0,
        "laterality": s(staging[7] if staging else None),

        # Receptor status
        "er_hscore": f(proteins.get("ESR1")),
        "pr_hscore": f(proteins.get("PGR")),
        "her2_hscore": f(proteins.get("ERBB2")),
        "ki67_index": f(cc[0] if cc else None),

        # DNA repair
        "brca1_status": s(dna[0] if dna else None),
        "brca2_status": s(dna[1] if dna else None),
        "mmr_status": s(dna[2] if dna else None),
        "tmb_score": f(dna[3] if dna else None),
        "hrd_score": f(dna[4] if dna else None),
        "pole_mutation": b(dna[5] if dna else None),

        # Immune
        "cd8_pct": f(immune[0] if immune else None),
        "m2_pct": f(immune[1] if immune else None),
        "treg_pct": f(immune[2] if immune else None),
        "pdl1_tps": f(chk[0] if chk else None),
        "pdl1_cps": f(chk[1] if chk else None),
        "tgf_beta": f(cyt[0] if cyt else None),
        "ifn_gamma": f(cyt[1] if cyt else None),

        # Hypoxia / TME
        "hif1a": f(hyp[0] if hyp else None),
        "o2_saturation": f(hyp[1] if hyp else None),
        "ifp": f(hyp[2] if hyp else None),
        "tumor_ph": f(hyp[3] if hyp else None),

        # Organ function
        "egfr": f(org[0] if org else None),
        "alt": f(org[1] if org else None),
        "bilirubin": f(org[2] if org else None),
        "albumin": f(org[3] if org else None),
        "lvef": f(org[4] if org else None),
        "qtc": f(org[5] if org else None),

        # Pharmacogenomics
        "cyp2d6": s(pgx[0] if pgx else None),
        "cyp3a4": s(pgx[1] if pgx else None),
        "ugt1a1": s(pgx[2] if pgx else None),
        "dpyd_variant": b(pgx[3] if pgx else None),
        "tpmt_activity": s(pgx[4] if pgx else None),

        # Body composition
        "bmi": f(body[0] if body else None),
        "smi": f(body[1] if body else None),

        # Microbiome
        "akkermansia": f(micro[0] if micro else None),
        "antibiotic_recent": b(micro[2] if micro else None),

        # Hormonal
        "estradiol": f(horm[0] if horm else None),

        # Liquid biopsy
        "ctdna_fraction": f(biopsy[0] if biopsy else None),
        "mrd_status": s(biopsy[1] if biopsy else None),

        # Mutations & resistance
        "actionable_mutations": raw.get("actionable_mutations") or [],
        "mdr1_expression": f(resist[0] if resist else None),
    }
