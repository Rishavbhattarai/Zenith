from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from inventory.db import close_pool, get_pool
from inventory.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    yield
    await close_pool()


app = FastAPI(title="Zenith Inventory Service", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
