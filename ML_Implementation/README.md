# AURA-EMS
### Context-Aware Campus Energy Demand Forecasting Framework using Heterogeneous Time-Series Fusion

**Team Project — BCA 3rd Year, Alliance University**

AURA-EMS helps Alliance University move from **reactive** energy billing to **proactive, context-aware** energy demand forecasting. The system fuses historical smart-meter data with academic-calendar and weather context to predict short-term campus power demand, flag upcoming peak-load risk windows, and give facilities teams enough lead time to shift or defer non-critical loads — reducing BESCOM peak-tariff penalties and operational waste.

---

## 1. Problem Statement

Modern campuses behave like micro-cities: academic blocks peak during the day, hostels peak early morning and late night, and demand shifts sharply around exams, holidays, and weather changes. Traditional energy tracking looks only at past billing data and reacts after the fact.

**AURA-EMS asks:** *How can Alliance University transition from reactive energy tracking to proactive, context-aware demand forecasting using data science?*

We answer this by fusing:
- Historical smart-meter time-series data (kW / kVA)
- Academic calendar signals (weekday/weekend, vacation, exam cycles)
- Weather data (temperature)

...into a predictive ML pipeline that outputs short-term demand forecasts and peak-risk alerts through a live dashboard.

---

## 2. System Architecture

```
[Smart-Meter Data] + [Academic Calendar] + [Weather Feed]
                    │
                    ▼
        Module 1: Data Ingestion & Feature Engineering  (Likitha)
                    │  (model.pkl, metrics.json, inference CSV)
                    ▼
        Module 2: Database + FastAPI Backend             (Anushka)
                    │  (REST API: /health, /metrics, /forecasts, /peaks)
                    ▼
        Module 3: Streamlit Forecast Dashboard            (Risha)
```

**Integration rule:** the frontend never reads Likitha's CSV/pickle directly and never touches the database. It only consumes Anushka's REST API. This keeps each module independently replaceable and mirrors how real production systems are structured.

---

## 3. Team & Ownership

| Member | Module | Branch | Responsibility |
|---|---|---|---|
| **Likitha Srinivas** | AI / ML | `feature/ml-forecasting` | Data cleaning, leak-safe feature engineering, model training (baseline, XGBoost, LightGBM), evaluation, exporting `aura_ems_best.pkl`, `metrics.json`, `dashboard_inference_feed.csv` |
| **Anushka Ghosh** | Backend & Database | `feature/backend-api` | SQLite schema, seed pipeline, FastAPI endpoints, model registry, CORS setup — serves everything as clean JSON |
| **Risha Madhuri** | Frontend / Dashboard | `feature/frontend-dashboard` | Streamlit dashboard: KPI cards, actual-vs-predicted chart, peak-risk panel, filters, error handling |

Each member owns their folder and branch exclusively. No one edits another member's files directly — integration happens through the agreed contracts below.

---

## 4. Tech Stack (Frozen)

| Layer | Technology |
|---|---|
| ML | Python, pandas, NumPy, scikit-learn, XGBoost, LightGBM, joblib |
| Backend | FastAPI, SQLAlchemy, SQLite, Pydantic |
| Frontend | Streamlit, Plotly, `requests` |
| Versioning | Git + GitHub (feature-branch workflow) |

> Stack changes require team agreement — do not swap frameworks mid-project without informing the others.

---

## 5. Repository Structure

```
AURA-EMS/
├── ml/                        # Likitha
│   ├── feature_engineering.py
│   ├── train.py
│   ├── evaluate.py
│   ├── utils.py
│   ├── data/
│   ├── models/
│   ├── reports/
│   ├── outputs/
│   └── requirements-ml.txt
│
├── backend/                   # Anushka
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routers/
│   │   └── services/
│   ├── scripts/seed_db.py
│   ├── requirements-backend.txt
│   └── README_BACKEND.md
│
├── frontend/                  # Risha
│   ├── app.py
│   ├── components/
│   ├── services/
│   │   ├── api_client.py
│   │   └── config.py
│   ├── requirements-frontend.txt
│   └── README_FRONTEND.md
│
└── README.md                  # this file
```

---

## 6. API Contract (Backend ↔ Frontend)

Base URL: `http://127.0.0.1:8000`

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/metrics/summary` | Active model + RMSE / MAPE / MAE |
| GET | `/forecasts?start=...&end=...` | Actual vs predicted demand series |
| GET | `/forecasts/peaks?limit=10` | Top peak-risk intervals (HIGH/MEDIUM/LOW) |
| POST | `/predict` *(optional)* | On-demand single prediction |

Field names in these responses are **frozen** once Risha starts building against them. Any schema change must be communicated immediately — see each member's role guide for full request/response examples.

---

## 7. Getting Started

### Clone the repo
```bash
git clone <repo-url>
cd AURA-EMS
```

### 1) ML pipeline (Likitha)
```bash
cd ml
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements-ml.txt
python feature_engineering.py
python train.py
python evaluate.py
```

### 2) Backend (Anushka)
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements-backend.txt
python scripts/seed_db.py
uvicorn app.main:app --reload --port 8000
```
Verify: `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/docs`

### 3) Frontend (Risha)
```bash
cd frontend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements-frontend.txt
streamlit run app.py
```
> Backend must be running on port 8000 before starting the dashboard.

---

## 8. Git Workflow

`main` is protected and only receives changes through pull requests.

**Each member, on their own machine:**
```bash
git checkout main
git pull origin main
git checkout -b feature/<your-branch-name>
# ... do your work ...
git add .
git commit -m "feat(scope): short description"
git push -u origin feature/<your-branch-name>
```
Then open a Pull Request into `main` on GitHub.

**Branches for this project:**
- `feature/ml-forecasting` — Likitha
- `feature/backend-api` — Anushka
- `feature/frontend-dashboard` — Risha

**Recommended merge order:** ML → Backend → Frontend (each stage depends on the previous one's output).

---

## 9. Definition of Done (Project-Level)

- [ ] ML pipeline produces best model + metrics + inference CSV
- [ ] Backend seeds DB from ML outputs and serves all 4 endpoints correctly
- [ ] Frontend consumes only the backend API (no direct CSV/pickle access)
- [ ] Dashboard shows KPIs, actual-vs-predicted chart, and peak-risk panel
- [ ] Clear error states if backend is down
- [ ] Each module has its own README with exact run steps
- [ ] All three feature branches merged into `main` via PR

---

## 10. Value Proposition

- **Peak Demand Mitigation** — up to 24 hours' advance warning on load spikes, enabling manual load balancing to avoid BESCOM peak-tariff penalties.
- **Resource Allocation** — data-driven insights for HVAC/lighting scheduling based on predicted usage.
- **Academic Impact** — a production-shaped (not notebook-only) demonstration of applied predictive analytics.

---

## 11. Disclaimer

This is an academic capstone project built for demonstration purposes. It is a decision-support tool and is **not** a replacement for official BESCOM billing systems.
