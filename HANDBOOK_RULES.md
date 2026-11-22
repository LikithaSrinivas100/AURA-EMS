# AURA-EMS Review-03 — registered rules (agent + lead)

## 1. Mission
Close Review-02 gap: live-feeling dashboard (replay, zones, alerts), scientifically honest (baselines, peak metrics, leak-safe split, **simulated data** labelled), tested (report claims ↔ numbered tests). Rigor over random features.

## 2. Ground rules
1. Never shuffle time — train past, test future.
2. Never invent numbers — only script outputs.
3. Label data **simulated** in README, API notes, footer — never “real meter data”.
4. Keep existing API field names; else note in CHANGES.md for report writer.
5. Branch `feature/review-03-addons` only — no push to `main` before freeze.
6. Public demo stays open (no login).
7. No secrets in Git (`git ls-files | grep -i env`).
8. Don’t edit tests to force pass — fix code or KNOWN_ISSUES.md.
9. Official values in config with `value`, `source`, `year`, `status`; keep 0.71 / ₹8.50 / 21 as placeholders status `TO BE VERIFIED`.
10. One item → one commit → one passing test run.

## 3. Workflow
- One item wrapper: `Implement ONLY this item: …`
- Rules: no shuffle, no invented numbers, keep API names, pytest, run tests, **commit local, do not push**.
- Report: files changed + every new number → **stop**.
- If crash: continue from last commit, same rules.
- Lead verifies UI after each item (don’t trust agent “done”).

## 4. Schedule (order; lead paces)
| # | Work | Cut? |
|---|---|---|
| 0 | Recon + both services start | never |
| F1 | Baselines + peak-alert metrics | never |
| F2 | Zone drill-down | local |
| F3 | Replay mode | local |
| F4 | CSV export | local |
| F5 | Ingestion + gaps | local |
| F6 | Alert panel | local |
| 7 | Tests green + polish | cut 2nd (polish only) |
| 8 | Freeze / merge / deploy once | — |
| 9 | Facts + screenshots | — |
| 10 | Demo rehearsal | — |

**Never cut:** F1, F2, F3, F5, tests.

## 5. Artifacts + API URL (recon notes)
- **Canonical ML outputs:** `ML_Implementation/outputs/` (esp. `metrics.json`, `dashboard_inference_feed.csv`). Backend `data|models|outputs` are copies — can go **stale**.
- **After every ML change:** from `backend/`: `python scripts/seed_db.py` → then `GET /metrics/summary` must match `ML_Implementation/outputs/metrics.json` winner RMSE/MAPE/MAE (no invented numbers).
- **Frontend API:** `frontend/services/config.py` reads `API_BASE_URL` or `AURA_BACKEND_URL` env; default `http://127.0.0.1:8000`.
