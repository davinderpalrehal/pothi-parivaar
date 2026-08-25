import os

# Local `python run.py` is API + /docs. The Vue app is Vite on :5173.
# Production: uvicorn app.main:app (default POTHI_SERVE_FRONTEND=1) still
# serves frontend/dist when a build exists.
os.environ.setdefault("POTHI_SERVE_FRONTEND", "0")

import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.app_name} on http://{settings.host}:{settings.port} ...")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
