"""Standalone entry point for the live screen (without voice/dashboard).

    uvicorn src.live.app:app --host 0.0.0.0 --port 8000     ->  http://localhost:8000/live

The combined app (src/app.py, claude-03) mounts the same router next to /call and /dashboard.
"""
from __future__ import annotations

import fastapi
import fastapi.responses

from src.live.router import router

app = fastapi.FastAPI(title="DawnDispatch Live")
app.include_router(router)


@app.get("/", include_in_schema=False)
async def index():
    return fastapi.responses.RedirectResponse("/live")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "DawnDispatch Live"}
