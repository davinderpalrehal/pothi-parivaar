from pathlib import Path
from pydantic import BaseModel
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "frontend" / "dist"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseModel):
    app_name: str = "Pothi Parivaar"
    database_url: str = os.getenv(
        "POTHI_DB_URL", f"sqlite:///{DATA_DIR / 'pothi.db'}"
    )
    host: str = os.getenv("POTHI_HOST", "0.0.0.0")
    port: int = int(os.getenv("POTHI_PORT", "8000"))
    serve_frontend: bool = os.getenv("POTHI_SERVE_FRONTEND", "1").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]


settings = Settings()
