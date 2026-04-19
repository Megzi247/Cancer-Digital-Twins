-- ============================================================
-- CANCER DIGITAL TWIN — CLICKHOUSE CREATE TABLE STATEMENTS
-- 49 tables | MergeTree engine family
-- ============================================================

-- ============================================================
-- REFERENCE TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS drug
(
    drug_id             UUID,
    generic_name        String,
    brand_name          Nullable(String),
    drugbank_id         Nullable(String),
    drug_class          LowCardinality(String),
    mechanism_of_action Nullable(String),
    primary_target      Nullable(String),
    target_pathway      Nullable(String),
    molecular_weight    Nullable(Float32),
    formula             Nullable(String),
    logp                Nullable(Float32),
    is_prodrug          UInt8
)
ENGINE = ReplacingMergeTree()
ORDER BY drug_id;

CREATE TABLE IF NOT EXISTS drug_pk_profile
(
    pk_id                    UUID,
    drug_id                  UUID,
    population               Nullable(String),
    cmax_ug_ml               Nullable(Float32),
    tmax_h                   Nullable(Float32),
    auc_ug_h_ml              Nullable(Float32),
    half_life_h              Nullable(Float32),
    volume_distribution_l_kg Nullable(Float32),
    clearance_l_h_kg         Nullable(Float32),
    bioavailability_pct      Nullable(Float32),
    protein_binding_pct      Nullable(Float32),
    primary_elimination      LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (drug_id, pk_id);

CREATE TABLE IF NOT EXISTS drug_resistance_profile
(
    drp_id               UUID,
    drug_id              UUID,
    resistance_mechanism LowCardinality(String),
    gene_involved        Nullable(String),
    mutation_description Nullable(String),
    resistance_frequency Nullable(Float32),
    subsequent_therapy   Nullable(String)
)
ENGINE = MergeTree()
ORDER BY (drug_id, drp_id);

CREATE TABLE IF NOT EXISTS drug_interaction
(
    ddi_id           UUID,
    drug_a_id        UUID,
    drug_b_id        UUID,
    interaction_type LowCardinality(String),
    direction        LowCardinality(String),
    severity         LowCardinality(String),
    mechanism        Nullable(String),
    auc_change_pct   Nullable(Float32),
    data_source      Nullable(String)
)
ENGINE = MergeTree()
ORDER BY (drug_a_id, drug_b_id);

CREATE TABLE IF NOT EXISTS combination_synergy
(
    syn_id         UUID,
    drug_a_id      UUID,
    drug_b_id      UUID,
    cancer_type    Nullable(String),
    cell_line      Nullable(String),
    synergy_score  Nullable(Float32),
    synergy_method LowCardinality(String),
    antagonism_flag UInt8,
    data_source    Nullable(String)
)
ENGINE = MergeTree()
ORDER BY (drug_a_id, drug_b_id);

-- ============================================================
-- LAYER 1 — MOLECULAR & GENOMIC
-- ============================================================

CREATE TABLE IF NOT EXISTS patient
(
    patient_id   UUID,
    mrn          String,
    date_of_birth Date32,
    biological_sex LowCardinality(String),
    ethnicity    Nullable(String),
    ancestry_panel Nullable(String),
    created_at   DateTime,
    updated_at   DateTime
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY patient_id;

CREATE TABLE IF NOT EXISTS genomic_sample
(
    sample_id           UUID,
    patient_id          UUID,
    sample_type         LowCardinality(String),
    tissue_site         Nullable(String),
    collection_date     Nullable(Date),
    sequencing_platform Nullable(String),
    tumor_purity        Nullable(Float32),
    passage_number      Nullable(Int16),
    preservation_method LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (patient_id, sample_id);

CREATE TABLE IF NOT EXISTS somatic_mutation
(
    mutation_id           UUID,
    sample_id             UUID,
    gene_symbol           String,
    chromosome            LowCardinality(String),
    position              Int64,
    ref_allele            String,
    alt_allele            String,
    mutation_type         LowCardinality(String),
    consequence           Nullable(String),
    hgvs_protein          Nullable(String),
    vaf                   Float32,
    read_depth            Nullable(Int32),
    clinical_significance LowCardinality(String),
    cosmic_id             Nullable(String),
    oncokb_level          Nullable(String),
    mutational_signature  Nullable(String)
)
ENGINE = MergeTree()
ORDER BY (sample_id, gene_symbol, chromosome, position);

CREATE TABLE IF NOT EXISTS copy_number_variant
(
    cnv_id          UUID,
    sample_id       UUID,
    gene_symbol     Nullable(String),
    chromosome      LowCardinality(String),
    start_pos       Int64,
    end_pos         Int64,
    copy_number     Nullable(Float32),
    log2_ratio      Nullable(Float32),
    cnv_type        LowCardinality(String),
    ploidy_adjusted UInt8
)
ENGINE = MergeTree()
ORDER BY (sample_id, chromosome, start_pos);

CREATE TABLE IF NOT EXISTS gene_expression
(
    expr_id         UUID,
    sample_id       UUID,
    gene_id         String,
    gene_symbol     Nullable(String),
    tpm             Nullable(Float32),
    fpkm            Nullable(Float32),
    raw_count       Nullable(Int32),
    z_score         Nullable(Float32),
    percentile_rank Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, gene_id);

CREATE TABLE IF NOT EXISTS epigenetic_mark
(
    epi_id         UUID,
    sample_id      UUID,
    mark_type      LowCardinality(String),
    locus          String,
    beta_value     Nullable(Float32),
    m_value        Nullable(Float32),
    gene_symbol    Nullable(String),
    region_context LowCardinality(String),
    chip_signal    Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, mark_type, locus);

CREATE TABLE IF NOT EXISTS protein_expression
(
    prot_id               UUID,
    sample_id             UUID,
    protein_name          String,
    uniprot_id            Nullable(String),
    quantification_method LowCardinality(String),
    expression_level      Nullable(Float32),
    h_score               Nullable(Float32),
    allred_score          Nullable(Int8),
    phosphorylation_site  Nullable(String)
)
ENGINE = MergeTree()
ORDER BY (sample_id, protein_name);

CREATE TABLE IF NOT EXISTS ncrna_profile
(
    ncrna_id         UUID,
    sample_id        UUID,
    rna_type         LowCardinality(String),
    rna_id           String,
    name             Nullable(String),
    expression_level Float32,
    target_genes     Nullable(String)
)
ENGINE = MergeTree()
ORDER BY (sample_id, rna_type, rna_id);

CREATE TABLE IF NOT EXISTS metabolomics_profile
(
    metab_id         UUID,
    sample_id        UUID,
    metabolite_name  String,
    hmdb_id          Nullable(String),
    kegg_id          Nullable(String),
    concentration    Float32,
    platform         LowCardinality(String),
    metabolite_class LowCardinality(String),
    z_score          Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, metabolite_name);

-- ============================================================
-- LAYER 2 — TUMOR CELL BIOLOGY
-- ============================================================

CREATE TABLE IF NOT EXISTS tumor_clone
(
    clone_id              UUID,
    sample_id             UUID,
    clone_label           String,
    cancer_cell_fraction  Float32,
    driver_mutations      Nullable(String),
    is_founder_clone      UInt8,
    phylogenetic_order    Nullable(Int16),
    selection_coefficient Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, clone_id);

CREATE TABLE IF NOT EXISTS cell_cycle_state
(
    ccs_id              UUID,
    sample_id           UUID,
    g1_fraction         Nullable(Float32),
    s_fraction          Nullable(Float32),
    g2m_fraction        Nullable(Float32),
    quiescent_fraction  Nullable(Float32),
    ki67_index          Float32,
    doubling_time_hours Nullable(Float32),
    mitotic_index       Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, ccs_id);

CREATE TABLE IF NOT EXISTS apoptosis_marker
(
    apop_id             UUID,
    sample_id           UUID,
    bcl2_expression     Nullable(Float32),
    bcl_xl_expression   Nullable(Float32),
    bax_expression      Nullable(Float32),
    bcl2_bax_ratio      Nullable(Float32),
    caspase3_activity   Nullable(Float32),
    tunel_positive_pct  Nullable(Float32),
    survivin_expression Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, apop_id);

CREATE TABLE IF NOT EXISTS dna_repair_status
(
    dna_id       UUID,
    sample_id    UUID,
    brca1_status LowCardinality(String),
    brca2_status LowCardinality(String),
    mmr_status   LowCardinality(String),
    msi_score    Nullable(Float32),
    tmb_score    Nullable(Float32),
    hrd_score    Nullable(Float32),
    pole_mutation UInt8,
    atm_status   Nullable(String)
)
ENGINE = MergeTree()
ORDER BY (sample_id, dna_id);

CREATE TABLE IF NOT EXISTS metabolic_phenotype
(
    met_id                    UUID,
    sample_id                 UUID,
    warburg_score             Nullable(Float32),
    glucose_uptake_rate       Nullable(Float32),
    glutamine_dependency      Nullable(Float32),
    lipid_synthesis_rate      Nullable(Float32),
    ros_level                 Nullable(Float32),
    nadh_nadph_ratio          Nullable(Float32),
    oxidative_phosph_fraction Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, met_id);

CREATE TABLE IF NOT EXISTS stemness_profile
(
    stem_id          UUID,
    sample_id        UUID,
    cd44_expression  Nullable(Float32),
    cd24_expression  Nullable(Float32),
    cd133_expression Nullable(Float32),
    aldh_activity    Nullable(Float32),
    stemness_index   Nullable(Float32),
    emt_score        Nullable(Float32),
    nanog_expression Nullable(Float32),
    oct4_expression  Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, stem_id);

CREATE TABLE IF NOT EXISTS drug_resistance_feature
(
    resist_id            UUID,
    sample_id            UUID,
    mdr1_expression      Nullable(Float32),
    mrp1_expression      Nullable(Float32),
    bcrp_expression      Nullable(Float32),
    top2a_expression     Nullable(Float32),
    resistance_mutations Nullable(String),
    pgp_activity         Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, resist_id);

-- ============================================================
-- LAYER 3 — TUMOR MICROENVIRONMENT
-- ============================================================

CREATE TABLE IF NOT EXISTS immune_infiltration
(
    inf_id                  UUID,
    sample_id               UUID,
    cd8_t_cells_pct         Nullable(Float32),
    cd4_t_cells_pct         Nullable(Float32),
    regulatory_t_cells_pct  Nullable(Float32),
    nk_cells_pct            Nullable(Float32),
    b_cells_pct             Nullable(Float32),
    macrophage_m1_pct       Nullable(Float32),
    macrophage_m2_pct       Nullable(Float32),
    dendritic_cells_pct     Nullable(Float32),
    neutrophils_pct         Nullable(Float32),
    quantification_method   LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (sample_id, inf_id);

CREATE TABLE IF NOT EXISTS checkpoint_expression
(
    chk_id           UUID,
    sample_id        UUID,
    pdl1_tps         Nullable(Float32),
    pdl1_cps         Nullable(Float32),
    pdl2_expression  Nullable(Float32),
    ctla4_expression Nullable(Float32),
    tim3_expression  Nullable(Float32),
    lag3_expression  Nullable(Float32),
    tigit_expression Nullable(Float32),
    cd47_expression  Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, chk_id);

CREATE TABLE IF NOT EXISTS cytokine_milieu
(
    cyt_id          UUID,
    sample_id       UUID,
    il6_level       Nullable(Float32),
    il10_level      Nullable(Float32),
    il2_level       Nullable(Float32),
    tnf_alpha_level Nullable(Float32),
    ifn_gamma_level Nullable(Float32),
    tgf_beta_level  Nullable(Float32),
    cxcl10_level    Nullable(Float32),
    vegf_level      Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, cyt_id);

CREATE TABLE IF NOT EXISTS stromal_composition
(
    strom_id             UUID,
    sample_id            UUID,
    caf_fraction         Nullable(Float32),
    pericyte_fraction    Nullable(Float32),
    endothelial_fraction Nullable(Float32),
    stromal_score        Nullable(Float32),
    collagen_density     Nullable(Float32),
    stiffness_kpa        Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, strom_id);

CREATE TABLE IF NOT EXISTS ecm_profile
(
    ecm_id                UUID,
    sample_id             UUID,
    fibronectin_level     Nullable(Float32),
    laminin_level         Nullable(Float32),
    hyaluronic_acid_level Nullable(Float32),
    mmp2_activity         Nullable(Float32),
    mmp9_activity         Nullable(Float32),
    tissue_inhibitor_timp Nullable(Float32),
    collagen_crosslinking Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, ecm_id);

CREATE TABLE IF NOT EXISTS hypoxia_vasculature
(
    hyp_id                      UUID,
    sample_id                   UUID,
    hif1a_expression            Nullable(Float32),
    ca9_expression              Nullable(Float32),
    o2_saturation_pct           Nullable(Float32),
    hypoxia_gene_signature      Nullable(Float32),
    vessel_density              Nullable(Float32),
    vegf_a_level                Nullable(Float32),
    mvd_score                   Nullable(Float32),
    interstitial_fluid_pressure Nullable(Float32),
    tumor_ph                    Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (sample_id, hyp_id);

-- ============================================================
-- LAYER 4 — PATIENT PHYSIOLOGY
-- ============================================================

CREATE TABLE IF NOT EXISTS organ_function
(
    organ_id          UUID,
    patient_id        UUID,
    assessment_date   Date,
    egfr_ml_min       Nullable(Float32),
    creatinine_umol_l Nullable(Float32),
    alt_u_l           Nullable(Float32),
    ast_u_l           Nullable(Float32),
    bilirubin_umol_l  Nullable(Float32),
    albumin_g_l       Nullable(Float32),
    lvef_pct          Nullable(Float32),
    qtc_ms            Nullable(Float32),
    inr               Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);

CREATE TABLE IF NOT EXISTS immune_baseline
(
    imm_id            UUID,
    patient_id        UUID,
    assessment_date   Date,
    wbc_count         Nullable(Float32),
    lymphocyte_count  Nullable(Float32),
    neutrophil_count  Nullable(Float32),
    nlr               Nullable(Float32),
    cd4_count         Nullable(Float32),
    cd8_count         Nullable(Float32),
    nk_cell_count     Nullable(Float32),
    igg_level         Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);

CREATE TABLE IF NOT EXISTS hormonal_profile
(
    horm_id           UUID,
    patient_id        UUID,
    assessment_date   Date,
    estradiol_pmol_l  Nullable(Float32),
    testosterone_nmol_l Nullable(Float32),
    cortisol_nmol_l   Nullable(Float32),
    insulin_pmol_l    Nullable(Float32),
    igf1_nmol_l       Nullable(Float32),
    thyroid_tsh       Nullable(Float32),
    dhea_s_umol_l     Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);

CREATE TABLE IF NOT EXISTS pharmacogenomics
(
    pgx_id           UUID,
    patient_id       UUID,
    cyp2d6_phenotype LowCardinality(String),
    cyp3a4_phenotype LowCardinality(String),
    cyp2c19_phenotype LowCardinality(String),
    ugt1a1_status    Nullable(String),
    tpmt_activity    LowCardinality(String),
    dpyd_variant     UInt8,
    slc28a3_variant  Nullable(String)
)
ENGINE = ReplacingMergeTree()
ORDER BY (patient_id, pgx_id);

CREATE TABLE IF NOT EXISTS body_composition
(
    body_id               UUID,
    patient_id            UUID,
    assessment_date       Date,
    bmi                   Nullable(Float32),
    skeletal_muscle_index Nullable(Float32),
    body_fat_pct          Nullable(Float32),
    visceral_fat_area     Nullable(Float32),
    weight_kg             Nullable(Float32),
    height_cm             Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);

CREATE TABLE IF NOT EXISTS microbiome_profile
(
    micro_id              UUID,
    patient_id            UUID,
    sample_date           Date,
    site                  LowCardinality(String),
    sequencing_method     LowCardinality(String),
    shannon_diversity     Nullable(Float32),
    firmicutes_ratio      Nullable(Float32),
    akkermansia_abundance Nullable(Float32),
    dominant_taxa         Nullable(String),
    antibiotic_recent     UInt8
)
ENGINE = MergeTree()
ORDER BY (patient_id, sample_date);

-- ============================================================
-- LAYER 5 — CLINICAL & TREATMENT HISTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS tumor_staging
(
    stage_id           UUID,
    patient_id         UUID,
    staging_date       Date,
    cancer_type        String,
    primary_site       String,
    histology          Nullable(String),
    t_stage            String,
    n_stage            String,
    m_stage            String,
    ajcc_overall_stage String,
    grade              Nullable(Int8),
    laterality         LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (patient_id, staging_date);

CREATE TABLE IF NOT EXISTS imaging_measurement
(
    img_id              UUID,
    patient_id          UUID,
    scan_date           Date,
    modality            LowCardinality(String),
    lesion_id           String,
    lesion_site         Nullable(String),
    longest_diameter_mm Nullable(Float32),
    volume_mm3          Nullable(Float32),
    suv_max             Nullable(Float32),
    recist_response     LowCardinality(String),
    radiomics_features  Nullable(String)
)
ENGINE = MergeTree()
ORDER BY (patient_id, scan_date, lesion_id);

CREATE TABLE IF NOT EXISTS treatment_regimen
(
    regimen_id             UUID,
    patient_id             UUID,
    line_of_therapy        Int8,
    regimen_name           String,
    treatment_intent       LowCardinality(String),
    start_date             Date,
    end_date               Nullable(Date),
    discontinuation_reason LowCardinality(String),
    best_response          LowCardinality(String),
    pfs_days               Nullable(Int32)
)
ENGINE = MergeTree()
ORDER BY (patient_id, start_date);

CREATE TABLE IF NOT EXISTS treatment_drug_dose
(
    admin_id           UUID,
    regimen_id         UUID,
    drug_id            UUID,
    administration_date Date,
    planned_dose_mg_m2 Nullable(Float32),
    actual_dose_mg_m2  Nullable(Float32),
    dose_reduction_pct Nullable(Float32),
    route              LowCardinality(String),
    cycle_number       Nullable(Int16),
    infusion_duration_h Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (regimen_id, administration_date, drug_id);

CREATE TABLE IF NOT EXISTS adverse_event
(
    ae_id           UUID,
    patient_id      UUID,
    regimen_id      Nullable(UUID),
    ae_term         String,
    ctcae_grade     Int8,
    onset_date      Nullable(Date),
    resolution_date Nullable(Date),
    attribution     LowCardinality(String),
    action_taken    LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (patient_id, onset_date, ae_term)
SETTINGS allow_nullable_key = 1;

CREATE TABLE IF NOT EXISTS liquid_biopsy
(
    lbx_id              UUID,
    patient_id          UUID,
    collection_date     Date,
    ctdna_fraction      Nullable(Float32),
    ctdna_copies_ml     Nullable(Float32),
    ctc_count           Nullable(Int32),
    detected_mutations  Nullable(String),
    mrd_status          LowCardinality(String),
    ctdna_half_life     Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (patient_id, collection_date);

CREATE TABLE IF NOT EXISTS pathology_report
(
    path_id                 UUID,
    patient_id              UUID,
    report_date             Date,
    specimen_type           LowCardinality(String),
    margin_status           LowCardinality(String),
    lymph_nodes_positive    Nullable(Int16),
    lymph_nodes_examined    Nullable(Int16),
    perineural_invasion     UInt8,
    lymphovascular_invasion UInt8,
    pathologic_response_pct Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (patient_id, report_date);

CREATE TABLE IF NOT EXISTS performance_status
(
    ps_id           UUID,
    patient_id      UUID,
    assessment_date Date,
    ecog_score      Nullable(Int8),
    karnofsky_score Nullable(Int8),
    pain_score      Nullable(Int8),
    fatigue_score   Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);

CREATE TABLE IF NOT EXISTS patient_drug_pk
(
    ipk_id            UUID,
    patient_id        UUID,
    drug_id           UUID,
    admin_id          Nullable(UUID),
    timepoint_h       Float32,
    plasma_conc_ug_ml Nullable(Float32),
    tumor_conc_ug_g   Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (patient_id, drug_id, timepoint_h);

-- ============================================================
-- LAYER 6 — DRUG & EXTERNAL STIMULUS
-- ============================================================

CREATE TABLE IF NOT EXISTS radiation_plan
(
    rad_id                   UUID,
    patient_id               UUID,
    modality                 LowCardinality(String),
    target_volume            Nullable(String),
    total_dose_gy            Float32,
    fraction_dose_gy         Float32,
    fraction_count           Int16,
    treatment_days_per_week  Nullable(Int8),
    technique                LowCardinality(String),
    concurrent_sensitizer_id Nullable(UUID),
    oar_constraints          Nullable(String)
)
ENGINE = MergeTree()
ORDER BY (patient_id, rad_id);

-- ============================================================
-- LAYER 7 — ENVIRONMENT & LIFESTYLE
-- ============================================================

CREATE TABLE IF NOT EXISTS diet_nutrition
(
    diet_id              UUID,
    patient_id           UUID,
    assessment_date      Date,
    assessment_tool      LowCardinality(String),
    caloric_intake_kcal  Nullable(Float32),
    protein_g_day        Nullable(Float32),
    carb_g_day           Nullable(Float32),
    fat_g_day            Nullable(Float32),
    fiber_g_day          Nullable(Float32),
    red_meat_g_day       Nullable(Float32),
    processed_meat_g_day Nullable(Float32),
    alcohol_g_day        Nullable(Float32),
    dietary_pattern      LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);

CREATE TABLE IF NOT EXISTS physical_activity
(
    pa_id             UUID,
    patient_id        UUID,
    assessment_date   Date,
    met_min_week      Nullable(Float32),
    vigorous_min_week Nullable(Float32),
    moderate_min_week Nullable(Float32),
    sedentary_h_day   Nullable(Float32),
    vo2max_ml_kg_min  Nullable(Float32),
    steps_per_day     Nullable(Int32),
    muscle_strength_kg Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);

CREATE TABLE IF NOT EXISTS carcinogen_exposure
(
    exp_id                UUID,
    patient_id            UUID,
    smoking_status        LowCardinality(String),
    pack_years            Nullable(Float32),
    alcohol_units_week    Nullable(Float32),
    uv_exposure_index     Nullable(Float32),
    radon_bq_m3           Nullable(Float32),
    occupational_exposure Nullable(String),
    prior_radiation_gy    Nullable(Float32),
    prior_chemotherapy    UInt8
)
ENGINE = ReplacingMergeTree()
ORDER BY (patient_id, exp_id);

CREATE TABLE IF NOT EXISTS stress_psychology
(
    stress_id          UUID,
    patient_id         UUID,
    assessment_date    Date,
    perceived_stress_pss Nullable(Int16),
    phq9_depression    Nullable(Int16),
    gad7_anxiety       Nullable(Int16),
    hrv_sdnn_ms        Nullable(Float32),
    morning_cortisol   Nullable(Float32),
    sleep_hours_night  Nullable(Float32),
    insomnia_isi_score Nullable(Int16)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);

CREATE TABLE IF NOT EXISTS environmental_exposure
(
    env_id          UUID,
    patient_id      UUID,
    assessment_date Date,
    pm25_ug_m3      Nullable(Float32),
    no2_ppb         Nullable(Float32),
    air_quality_index Nullable(Float32),
    hpv_status      LowCardinality(String),
    hpv_genotype    Nullable(String),
    h_pylori_status LowCardinality(String),
    ebv_status      LowCardinality(String),
    ebv_vca_igg     Nullable(Float32),
    hbv_status      LowCardinality(String)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);

CREATE TABLE IF NOT EXISTS socioeconomic_context
(
    soc_id                  UUID,
    patient_id              UUID,
    assessment_date         Date,
    ses_index               Nullable(Float32),
    insurance_type          LowCardinality(String),
    healthcare_access_score Nullable(Float32),
    health_literacy_score   Nullable(Float32),
    social_support_score    Nullable(Float32),
    employment_status       LowCardinality(String),
    financial_toxicity_score Nullable(Float32),
    education_years         Nullable(Int8)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);

CREATE TABLE IF NOT EXISTS circadian_profile
(
    circ_id                UUID,
    patient_id             UUID,
    assessment_date        Date,
    chronotype             LowCardinality(String),
    sleep_efficiency_pct   Nullable(Float32),
    rem_sleep_pct          Nullable(Float32),
    melatonin_peak_time    Nullable(String),
    light_exposure_lux_day Nullable(Float32),
    night_shift_worker     UInt8,
    wrist_actigraphy_days  Nullable(Int16)
)
ENGINE = MergeTree()
ORDER BY (patient_id, assessment_date);
