from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.database import (
    init_db,
    seed_db,
    get_all_drivers,
    get_sessions_by_driver,
    get_most_aggressive_driver,
    get_sessions_by_label,
    compare_drivers,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_db()
    yield


app = FastAPI(
    title="Automotive Sensor Intelligence API",
    description="Query OBD-II driving session data",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/health")
def health():
    return {"status": "ok", "service": "automotive-sensor-api"}


@app.get("/drivers")
def get_drivers():
    results = get_all_drivers()
    if not results:
        raise HTTPException(status_code=404, detail="No drivers found")
    return results


@app.get("/drivers/{driver_id}/sessions")
def get_driver_sessions(driver_id: str):
    results = get_sessions_by_driver(driver_id)
    if not results:
        raise HTTPException(status_code=404, detail=f"No sessions found for driver {driver_id}")
    return results


@app.get("/drivers/aggressive")
def most_aggressive():
    results = get_most_aggressive_driver()
    if not results:
        raise HTTPException(status_code=404, detail="No data found")
    return results


@app.get("/sessions/{label}")
def sessions_by_label(label: str):
    results = get_sessions_by_label(label)
    if not results:
        raise HTTPException(status_code=404, detail=f"No sessions found with label {label}")
    return results


@app.get("/compare")
def compare():
    results = compare_drivers()
    if not results:
        raise HTTPException(status_code=404, detail="No data found")
    return results