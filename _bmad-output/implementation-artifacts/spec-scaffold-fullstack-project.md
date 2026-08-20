---
title: 'Scaffold Full-Stack Project (Backend + Frontend + DB Structure)'
type: 'feature'
created: '2026-08-20'
status: 'done'
baseline_commit: '43bf196cb7d9ce243dad4b3c05263f90ad2028e3'
review_loop_iteration: 0
context:
  - '_bmad-output/planning-artifacts/architecture/architecture-pothi-parivaar-2026-08-20/ARCHITECTURE-SPINE.md'
  - 'AGENTS.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Pothi Parivaar currently has planning documents and architecture specifications, but lacks the core runnable full-stack codebase, database layer, API endpoints, frontend application scaffold, and Hermes skill integration.

**Approach:** Scaffold the complete Layered Modular Monolith structure: FastAPI backend with SQLite (WAL mode) and SQLModel models, API routers for books, readers, locations, isbn, and hermes, a Vue 3 + Vuetify 3 frontend with Vite proxy, the standalone Hermes skill stub, and backend test suites.

## Boundaries & Constraints

**Always:**
- Use FastAPI (Python 3.11+) with Pydantic v2 schemas and explicit response models.
- Use SQLite in WAL mode (`PRAGMA journal_mode=WAL;`) with the database stored in `data/pothi.db`.
- Use Vue 3 + Vuetify 3 out-of-the-box Material Design components with zero custom CSS/theme overrides.
- Route backend APIs under `/api/v1/` (with compatibility redirects or mounts for `/api/*`).
- Never commit directly to `main`; work on `feat/scaffold-project`.

**Ask First:**
- Introducing external databases or heavyweight services beyond SQLite.
- Adding custom CSS stylesheets or design systems overriding Vuetify Material Design defaults.

**Never:**
- Multi-tenant auth or external Dockerized database clusters in V1.
- Breaking the dual manual/ISBN ingestion isolation (manual creation must work fully offline).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Health check | `GET /api/health` | `{"status": "ok", "app": "pothi-parivaar"}` | Standard 500 JSON if DB connection fails |
| Initialize DB & CRUD book | `POST /api/v1/books` with valid book payload | 201 Created with auto-increment integer ID and timestamps | 422 Unprocessable Entity for invalid schema |
| List books | `GET /api/v1/books` | 200 OK with array of books | Empty array `[]` when no books exist |
| Frontend Dev Server | `npm run dev` in `frontend/` | Serves SPA on Vite dev port, proxies `/api` calls to `:8000` | Fallback error alert if backend is unreachable |
| Hermes Skill Invocation | `pothi_skill.py` querying `http://localhost:8000/api/` | Returns structured summary JSON for LLM tool use | Graceful connection error message |

</frozen-after-approval>

## Code Map

- `requirements.txt` -- Python dependencies (FastAPI, SQLModel, Uvicorn, HTTPX, Pytest)
- `run.py` -- Top-level server launcher script
- `app/main.py` -- FastAPI app entrypoint, CORS setup, router mounting, static file serving
- `app/config.py` -- Application settings (DB path, server host/port, CORS)
- `app/database.py` -- SQLite engine with WAL mode, session factory, `init_db()`
- `app/models.py` -- SQLModel entities: `Book`, `Reader`, `ReadingSession`, `Location` and Pydantic schemas
- `app/api/books.py` -- Book CRUD and filtering endpoints
- `app/api/readers.py` -- Reader profiles and reading status endpoints
- `app/api/locations.py` -- Shelf and physical location endpoints
- `app/api/isbn.py` -- ISBN lookup advisory endpoint
- `app/api/hermes.py` -- Hermes AI assistant dedicated query & recommendation endpoints
- `app/services/book_service.py` -- Book domain business logic
- `app/services/isbn_service.py` -- External Open Library / Google Books resolver
- `app/services/recommend.py` -- Recommendation ranking logic
- `frontend/package.json` -- Vue 3, Vuetify 3, Vite, MDI fonts, Axios
- `frontend/vite.config.js` -- Vite configuration with Vuetify plugin and API proxy
- `frontend/index.html` -- HTML5 entrypoint with Google Fonts (Roboto) & MDI icons
- `frontend/src/main.js` -- Vue 3 bootstrap & Vuetify plugin registration
- `frontend/src/plugins/vuetify.js` -- Vuetify configuration with standard Material Design 3 theme
- `frontend/src/App.vue` -- Main layout (`v-app`, `v-app-bar`, `v-navigation-drawer`, `v-main`)
- `frontend/src/services/api.js` -- API client communicating with backend
- `hermes_skill/pothi_skill.py` -- Standalone Hermes tool/skill for VPS agent integration
- `tests/test_api.py` -- Pytest test suite for health and book CRUD

## Tasks & Acceptance

**Execution:**
- [x] `requirements.txt` -- Create Python dependencies file -- Required for FastAPI, SQLModel, and Uvicorn runtime
- [x] `app/config.py` & `app/database.py` -- Setup configuration and SQLite engine with WAL mode -- Ensures persistent database in `data/pothi.db`
- [x] `app/models.py` -- Define SQLModel data models and Pydantic DTOs -- Enforces schema consistency across backend
- [x] `app/services/book_service.py`, `app/services/isbn_service.py`, `app/services/recommend.py` -- Implement domain service functions -- Encapsulates core logic
- [x] `app/api/*.py` & `app/main.py` -- Implement FastAPI endpoints and app assembly -- Provides REST API under `/api/v1/` and health check
- [x] `run.py` -- Implement top-level dev server runner -- Easy startup for backend
- [x] `frontend/package.json`, `frontend/vite.config.js`, `frontend/index.html` -- Initialize Vite + Vue 3 + Vuetify 3 frontend -- Establishes SPA build toolchain
- [x] `frontend/src/plugins/vuetify.js`, `frontend/src/main.js`, `frontend/src/App.vue`, `frontend/src/services/api.js` -- Implement frontend foundation and core layout -- Provides Material Design 3 UI
- [x] `hermes_skill/pothi_skill.py` -- Create Hermes agent standalone skill -- Enables localhost AI agent integration
- [x] `tests/test_api.py` -- Write automated tests for backend API & database operations -- Verifies functionality and stability

**Acceptance Criteria:**
- Given a fresh environment with installed dependencies, when `pytest tests/` is run, then all backend tests pass successfully.
- Given the FastAPI backend running on port 8000, when `GET /api/health` is requested, then a 200 response with JSON `{"status": "ok", "app": "pothi-parivaar"}` is returned.
- Given the SQLite database initialized, when a book is created via `POST /api/v1/books`, then the record is saved to `data/pothi.db` and retrieved via `GET /api/v1/books`.
- Given the frontend project, when `npm run build` is executed, then Vite builds static production assets without errors.
- Given `hermes_skill/pothi_skill.py`, when imported and called, then it interacts cleanly with the API client functions.

## Design Notes

- SQLite WAL mode is enforced upon engine connection via SQLAlchemy event listeners:
  ```python
  @event.listens_for(Engine, "connect")
  def set_sqlite_pragma(dbapi_connection, connection_record):
      cursor = dbapi_connection.cursor()
      cursor.execute("PRAGMA journal_mode=WAL")
      cursor.execute("PRAGMA synchronous=NORMAL")
      cursor.close()
  ```
- Vuetify 3 uses `@mdi/font` for standard Material Design icons without custom CSS bloat.

## Verification

**Commands:**
- `pytest tests/` -- expected: All tests pass
- `python -c "from app.database import init_db; init_db()"` -- expected: Creates `data/pothi.db` with WAL mode
- `cd frontend && npm run build` -- expected: Vite production bundle builds cleanly in `frontend/dist`

## Suggested Review Order

**Core Application & Entrypoints**

- Application bootstrap, lifespan database initialization, and router mounting
  [`main.py:1`](../../app/main.py#L1)

- SQLite engine configuration with WAL mode pragma listeners
  [`database.py:1`](../../app/database.py#L1)

**Data Models & Domain Logic**

- SQLModel schemas for books, readers, reading sessions, and locations
  [`models.py:1`](../../app/models.py#L1)

- Catalog CRUD logic, search filtering, and pagination
  [`book_service.py:1`](../../app/services/book_service.py#L1)

- Open Library advisory metadata resolver with error resilience
  [`isbn_service.py:1`](../../app/services/isbn_service.py#L1)

**REST API Endpoints**

- Books endpoints for listing, search, creation, and updates
  [`books.py:1`](../../app/api/books.py#L1)

- Readers management and reading progress tracking
  [`readers.py:1`](../../app/api/readers.py#L1)

- Physical room/unit/shelf management and hierarchy summary
  [`locations.py:1`](../../app/api/locations.py#L1)

- Dedicated Hermes agent tool endpoints for library status & recommendations
  [`hermes.py:1`](../../app/api/hermes.py#L1)

**Frontend (Vue 3 + Vuetify 3 SPA)**

- Main layout, app bar, navigation drawer, and view coordination
  [`App.vue:1`](../../frontend/src/App.vue#L1)

- Material Design 3 book presentation card with shelf badges
  [`BookCard.vue:1`](../../frontend/src/components/BookCard.vue#L1)

- Dual ingestion modal with manual form and ISBN barcode lookup tabs
  [`AddBookDialog.vue:1`](../../frontend/src/components/AddBookDialog.vue#L1)

**Integrations & Tests**

- Standalone Hermes agent skill for localhost VPS integration
  [`pothi_skill.py:1`](../../hermes_skill/pothi_skill.py#L1)

- Full backend automated test suite verifying CRUD, health, and agent endpoints
  [`test_api.py:1`](../../tests/test_api.py#L1)

