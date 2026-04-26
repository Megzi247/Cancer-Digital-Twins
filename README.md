# OncoNexus AI

Personalised cancer drug response simulation for individual patients. A clinician selects a patient from a synthetic cohort, chooses a drug combination, and OncoNexus AI queries a ClickHouse database to assemble the patient's full biological profile — spanning molecular, immune, physiological, and lifestyle layers — then uses a selectable AI model (Claude or GPT-4o) to predict efficacy, toxicity, and resistance for that specific patient.

This is not a chatbot. Every prediction traces back to a specific database field.

---

## Demo Scenarios

Three scenarios that illustrate the system's core capabilities. Run these in order for a full demo.

### Scenario 1 — Clean recommendation
**Patient:** any HR+/HER2− patient (high ER H-score, low Ki-67)  
**Drugs:** letrozole + palbociclib · **Intent:** adjuvant  
**Expected:** ~70–80% response probability, low–moderate toxicity, medium resistance risk  
Shows the system working normally end-to-end.

### Scenario 2 — DDI hard stop
**Patient:** same as Scenario 1  
**Drugs:** tamoxifen + letrozole · **Intent:** adjuvant  
**Expected:** immediate red interaction banner — tamoxifen requires oestrogen which letrozole eliminates. The AI model is never called.  
Shows the safety gate working. This is the most striking demo moment.

### Scenario 3 — Personalised toxicity flag
Find a patient with a DPYD variant:
```sql
SELECT p.mrn, p.patient_id
FROM pharmacogenomics pg
JOIN patient p ON pg.patient_id = p.patient_id
WHERE pg.dpyd_variant = 1
LIMIT 1;
```
**Drug:** capecitabine · **Intent:** palliative  
**Expected:** high toxicity warning citing DPYD deficiency and fluoropyrimidine toxicity risk.  
Shows personalisation — same drug, different patient, different outcome.

---

## Architecture

### 7-layer patient profile

Each patient is represented across seven biological layers queried from ClickHouse before any AI call is made:

| Layer | Content |
|---|---|
| L1 — Molecular | Somatic mutations, copy number variants, protein expression (ER/PR/HER2), gene expression |
| L2 — Cell Biology | Ki-67, TMB, HRD score, BRCA1/2, MMR status, MDR1 efflux |
| L3 — Tumour Microenvironment | CD8+ T cells, PD-L1 TPS/CPS, TGF-β, IFN-γ, HIF-1α, tumour pH |
| L4 — Patient Physiology | eGFR, LVEF, QTc, CYP2D6/3A4, DPYD, TPMT, skeletal muscle index |
| L5 — Clinical History | AJCC staging, TNM, ctDNA fraction, MRD status |
| L6 — Therapeutic | Drug mechanism, PK parameters, DDI severity, combination synergy scores |
| L7 — Lifestyle | Smoking, prior chemotherapy, physical activity, stress/cortisol, chronotype, financial toxicity, social support |

### Simulation pipeline

```
Patient selected
    └─ Query ClickHouse across all 7 layers → patient feature vector
         └─ Fetch drug data (mechanism, PK, synergy)
              └─ DDI hard stop ← blocks here if contraindicated/major interaction
                   └─ Build structured prompt (feature vector + drug data)
                        └─ AI Call 1 → JSON (efficacy / toxicity / resistance)
                             └─ AI Call 2 → clinical narrative
                                  └─ Render results
```

### Safety gate

The drug–drug interaction check runs as a deterministic database query **before** the AI model is ever called. If any selected drug pair has `severity IN ('contraindicated', 'major')`, the simulation is blocked and the interaction mechanism is shown to the user. This check cannot be bypassed through the model.

---

## Tech Stack

| Component | Technology |
|---|---|
| Database | ClickHouse (self-hosted, native TCP port 9000) |
| AI (default) | Claude via aisuite (`anthropic:claude-opus-4-5`) |
| Alternative AI | GPT-4o via aisuite (`openai:gpt-4o`) |
| Interface | Streamlit |
| DB driver | `clickhouse-driver` (native protocol, not HTTP) |
| Language | Python 3.10+ |

---

## Getting Started

### Prerequisites

- Docker (for ClickHouse)
- Python 3.10+
- `uv` package manager
- Anthropic API key (and optionally OpenAI API key)

### 1. Start ClickHouse

```bash
docker run -d --name clickhouse \
  -p 9000:9000 -p 8123:8123 \
  -v $(pwd)/data:/var/lib/clickhouse \
  clickhouse/clickhouse-server
```

### 2. Load schema and data

```bash
clickhouse-client --query "CREATE DATABASE IF NOT EXISTS cancer_digital_twins"
clickhouse-client --database cancer_digital_twins < data_sql_queries/cancer_digital_twin_ddl.sql
clickhouse-client --database cancer_digital_twins < data_sql_queries/cancer_digital_twin_100_patients.sql
```

### 3. Install dependencies

```bash
uv sync
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials (see [Environment Variables](#environment-variables) below).

### 5. Run the app

```bash
uv run streamlit run app.py
```

---

## Project Structure

```
cancer_digital_twins/
├── app.py                          ← Streamlit entry point, session state, simulation orchestration
├── main.py                         ← project entry point
├── pyproject.toml                  ← dependencies and project metadata
├── uv.lock                         ← locked dependency versions
├── .env                            ← credentials (never commit)
├── .env.example                    ← credentials template
├── .python-version                 ← pinned Python version
├── .gitignore
├── image_background.png            ← background image for the UI
├── CLAUDE.md                       ← codebase context for Claude Code
├── .streamlit/
│   └── secrets.toml                ← Streamlit secrets (alternative to .env)
├── db/
│   ├── connection.py               ← thread-local ClickHouse client (one connection per thread, reads from .env or Streamlit secrets)
│   └── queries.py                  ← all SQL queries as functions
├── simulation/
│   ├── feature_builder.py          ← assembles patient feature vector from all 7 layers
│   ├── ddi_checker.py              ← DDI hard stop — runs before any AI call
│   ├── prompt_builder.py           ← constructs structured prompt from feature vector + drug data
│   └── simulator.py                ← aisuite calls, JSON parsing, narrative generation
├── ui/
│   ├── sidebar.py                  ← patient selector, drug multiselect, API key inputs, history
│   ├── patient_card.py             ← patient header, metric cards, molecular + physiology tables
│   └── results_panel.py            ← clinical context header, efficacy/toxicity/resistance cards, narrative
└── data_sql_queries/
    ├── cancer_digital_twin_ddl.sql          ← CREATE TABLE statements
    └── cancer_digital_twin_100_patients.sql ← 100 synthetic patient INSERT data
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `CLICKHOUSE_HOST` | Yes | ClickHouse host (default: `localhost`) |
| `CLICKHOUSE_PORT` | Yes | Native TCP port (default: `9000`) |
| `CLICKHOUSE_USER` | Yes | Database user |
| `CLICKHOUSE_PASSWORD` | Yes | Database password |
| `CLICKHOUSE_DATABASE` | Yes | Database name (default: `cancer_digital_twins`) |
| `ANTHROPIC_API_KEY` | Yes* | Required when using Claude (Anthropic) |
| `OPENAI_API_KEY` | No* | Required only if switching to GPT-4o in the UI |

*API keys can also be entered directly in the sidebar at runtime without setting them in `.env`.

---

## Synthetic Data

The database is pre-loaded with 100 synthetic breast cancer patients across five clinically realistic archetypes:

| Archetype | % of cohort |
|---|---|
| HR+/HER2− early | ~45% |
| HR+ metastatic | ~24% |
| Triple-negative (TNBC) | ~14% |
| HR+/HER2+ | ~9% |
| HER2+ HR− | ~8% |

All data is fully synthetic and does not represent any real individual.
