from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api import books, readers, locations, isbn, hermes
from app.config import settings, STATIC_DIR
from app.database import init_db
from app.models import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Pothi Parivaar - Personal & Family Physical Library Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """System health check endpoint."""
    return HealthResponse(status="ok", app="pothi-parivaar")


# Include API v1 routers
app.include_router(books.router, prefix="/api/v1")
app.include_router(readers.router, prefix="/api/v1")
app.include_router(locations.router, prefix="/api/v1")
app.include_router(isbn.router, prefix="/api/v1")
app.include_router(hermes.router, prefix="/api/v1")

# Also include /api/ aliases for convenience / direct agent tooling
app.include_router(books.router, prefix="/api")
app.include_router(readers.router, prefix="/api")
app.include_router(locations.router, prefix="/api")
app.include_router(isbn.router, prefix="/api")
app.include_router(hermes.router, prefix="/api")

# Production: one process on :8000 can serve the Vue build from frontend/dist.
# Local `python run.py` leaves this off so :8000 is API-only and / goes to /docs.
if (
    settings.serve_frontend
    and STATIC_DIR.exists()
    and (STATIC_DIR / "index.html").exists()
):
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:

    @app.get("/", include_in_schema=False)
    def root_to_docs() -> RedirectResponse:
        return RedirectResponse(url="/docs")
