from db.connection import get_client


def get_patient_list():
    client = get_client()
    return client.execute(
        "SELECT mrn, patient_id FROM patient ORDER BY mrn"
    )


def get_genomic_sample(patient_id: str):
    client = get_client()
    rows = client.execute(
        "SELECT sample_id, tumor_purity FROM genomic_sample WHERE patient_id = %(pid)s LIMIT 1",
        {"pid": patient_id},
    )
    return rows[0] if rows else None


def get_drug_ids(drug_names: list[str]):
    client = get_client()
    rows = client.execute(
        "SELECT drug_id, generic_name FROM drug WHERE generic_name IN %(names)s",
        {"names": drug_names},
    )
    return {row[1]: str(row[0]) for row in rows}


def get_drug_data(drug_ids: list[str]):
    client = get_client()
    drugs = client.execute(
        """
        SELECT d.drug_id, d.generic_name, d.drug_class, d.mechanism_of_action,
               d.primary_target, d.target_pathway
        FROM drug d
        WHERE d.drug_id IN %(ids)s
        """,
        {"ids": drug_ids},
    )
    synergy = client.execute(
        """
        SELECT drug_a_id, drug_b_id, synergy_score, antagonism_flag
        FROM combination_synergy
        WHERE drug_a_id IN %(ids)s AND drug_b_id IN %(ids)s
        """,
        {"ids": drug_ids},
    )
    return {"drugs": drugs, "synergy": synergy}


def check_ddi(drug_ids: list[str]):
    client = get_client()
    return client.execute(
        """
        SELECT di.severity, di.direction, di.mechanism,
               da.generic_name AS drug_a, db.generic_name AS drug_b
        FROM drug_interaction di
        JOIN drug da ON di.drug_a_id = da.drug_id
        JOIN drug db ON di.drug_b_id = db.drug_id
        WHERE (di.drug_a_id IN %(ids)s AND di.drug_b_id IN %(ids)s)
        """,
        {"ids": drug_ids},
    )


def get_patient_features(patient_id: str, sample_id: str):
    client = get_client()
    pid, sid = patient_id, sample_id

    demographics = client.execute(
        "SELECT date_of_birth, biological_sex FROM patient WHERE patient_id = %(pid)s LIMIT 1",
        {"pid": pid},
    )

    staging = client.execute(
        """
        SELECT cancer_type, histology, t_stage, n_stage, m_stage,
               ajcc_overall_stage, grade, laterality
        FROM tumor_staging WHERE patient_id = %(pid)s LIMIT 1
        """,
        {"pid": pid},
    )

    proteins = client.execute(
        """
        SELECT protein_name, h_score
        FROM protein_expression
        WHERE sample_id = %(sid)s AND protein_name IN ('ESR1','PGR','ERBB2')
        """,
        {"sid": sid},
    )

    cell_cycle = client.execute(
        "SELECT ki67_index, doubling_time_hours, mitotic_index FROM cell_cycle_state WHERE sample_id = %(sid)s LIMIT 1",
        {"sid": sid},
    )

    dna_repair = client.execute(
        """
        SELECT brca1_status, brca2_status, mmr_status, tmb_score, hrd_score, pole_mutation
        FROM dna_repair_status WHERE sample_id = %(sid)s LIMIT 1
        """,
        {"sid": sid},
    )

    immune = client.execute(
        "SELECT cd8_t_cells_pct, macrophage_m2_pct, regulatory_t_cells_pct FROM immune_infiltration WHERE sample_id = %(sid)s LIMIT 1",
        {"sid": sid},
    )

    checkpoint = client.execute(
        "SELECT pdl1_tps, pdl1_cps, ctla4_expression, lag3_expression FROM checkpoint_expression WHERE sample_id = %(sid)s LIMIT 1",
        {"sid": sid},
    )

    cytokine = client.execute(
        "SELECT tgf_beta_level, ifn_gamma_level, il10_level FROM cytokine_milieu WHERE sample_id = %(sid)s LIMIT 1",
        {"sid": sid},
    )

    hypoxia = client.execute(
        "SELECT hif1a_expression, o2_saturation_pct, interstitial_fluid_pressure, tumor_ph FROM hypoxia_vasculature WHERE sample_id = %(sid)s LIMIT 1",
        {"sid": sid},
    )

    organ = client.execute(
        """
        SELECT egfr_ml_min, alt_u_l, bilirubin_umol_l, albumin_g_l, lvef_pct, qtc_ms
        FROM organ_function WHERE patient_id = %(pid)s
        ORDER BY assessment_date DESC LIMIT 1
        """,
        {"pid": pid},
    )

    pgx = client.execute(
        "SELECT cyp2d6_phenotype, cyp3a4_phenotype, ugt1a1_status, dpyd_variant, tpmt_activity FROM pharmacogenomics WHERE patient_id = %(pid)s LIMIT 1",
        {"pid": pid},
    )

    body = client.execute(
        "SELECT bmi, skeletal_muscle_index, body_fat_pct FROM body_composition WHERE patient_id = %(pid)s LIMIT 1",
        {"pid": pid},
    )

    microbiome = client.execute(
        "SELECT akkermansia_abundance, shannon_diversity, antibiotic_recent FROM microbiome_profile WHERE patient_id = %(pid)s LIMIT 1",
        {"pid": pid},
    )

    hormonal = client.execute(
        "SELECT estradiol_pmol_l, testosterone_nmol_l FROM hormonal_profile WHERE patient_id = %(pid)s LIMIT 1",
        {"pid": pid},
    )

    biopsy = client.execute(
        """
        SELECT ctdna_fraction, mrd_status, detected_mutations
        FROM liquid_biopsy WHERE patient_id = %(pid)s
        ORDER BY collection_date DESC LIMIT 1
        """,
        {"pid": pid},
    )

    mutations = client.execute(
        """
        SELECT gene_symbol FROM somatic_mutation
        WHERE sample_id = %(sid)s AND oncokb_level IN ('1','2')
        """,
        {"sid": sid},
    )

    resistance = client.execute(
        "SELECT mdr1_expression FROM drug_resistance_feature WHERE sample_id = %(sid)s LIMIT 1",
        {"sid": sid},
    )

    return {
        "demographics": demographics[0] if demographics else None,
        "staging": staging[0] if staging else None,
        "proteins": {r[0]: r[1] for r in proteins},
        "cell_cycle": cell_cycle[0] if cell_cycle else None,
        "dna_repair": dna_repair[0] if dna_repair else None,
        "immune": immune[0] if immune else None,
        "checkpoint": checkpoint[0] if checkpoint else None,
        "cytokine": cytokine[0] if cytokine else None,
        "hypoxia": hypoxia[0] if hypoxia else None,
        "organ": organ[0] if organ else None,
        "pgx": pgx[0] if pgx else None,
        "body": body[0] if body else None,
        "microbiome": microbiome[0] if microbiome else None,
        "hormonal": hormonal[0] if hormonal else None,
        "biopsy": biopsy[0] if biopsy else None,
        "actionable_mutations": [r[0] for r in mutations],
        "resistance": resistance[0] if resistance else None,
    }
