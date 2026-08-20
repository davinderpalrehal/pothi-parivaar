# Agent Instructions — Pothi Parivaar

## Git & Development Workflow

- **Branching Policy**: Never commit directly to `main`.
- **Feature Branches**: Always cut a new branch from `main` (e.g. `feat/scaffold-fastapi-backend`, `feat/vue-vuetify-ui`, `feat/isbn-lookup`).
- **PR Workflow**: Complete the feature and tests on the branch, then prepare a PR / merge request against `main`.

## Technology Stack & Invariants

- **Backend**: FastAPI (Python 3.11+) + Pydantic v2 + Uvicorn
- **Database**: SQLite in WAL mode (`data/pothi.db`) using SQLModel / SQLAlchemy
- **Frontend**: Vue.js 3 + Vuetify 3 (Material Design 3 out-of-the-box, no custom themes/CSS) bundled with Vite
- **Hermes Agent Integration**: REST API on `localhost:8000/api/*` + standalone Hermes skill in `hermes_skill/pothi_skill.py`
