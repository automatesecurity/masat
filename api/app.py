"""MASAT API server (for the future UI portal).

This is a minimal job API:
- POST /scan  {target, scans?, smart?}
- GET  /runs

It stores completed runs in the same SQLite DB used by CLI --store.

Run:
  pip install -r requirements.txt -r requirements-api.txt
  uvicorn api.app:app --reload
"""

from __future__ import annotations

import asyncio
from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "FastAPI dependencies are not installed. Install with: pip install -r requirements-api.txt"
    ) from e

from scanners.registry import discover_scanners
from utils.targets import parse_target
from utils.workflows import plan_scans
from utils.schema import normalize_findings
from utils.history import default_db_path, store_run, list_runs, get_run
from utils.assets import default_assets_db_path, list_assets


app = FastAPI(title="MASAT API", version="0.1")

# Allow browser-based UI (Next.js) to call the API during local development.
# For production, restrict origins.
try:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"]
        ,
        allow_headers=["*"],
    )
except Exception:
    pass


class ScanRequest(BaseModel):
    target: str
    scans: str | None = None
    smart: bool = True
    store: bool = True
    db: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/scans")
def scans() -> dict[str, Any]:
    reg = discover_scanners()
    return {"scans": [{"id": k, "description": v.description} for k, v in reg.items()]}


@app.post("/scan")
async def scan(req: ScanRequest) -> dict[str, Any]:
    reg = discover_scanners()
    info = parse_target(req.target)

    if req.scans:
        scans_set = {s.strip() for s in req.scans.split(",") if s.strip()}
    elif req.smart:
        scans_set = set(plan_scans(info).scans)
    else:
        raise HTTPException(status_code=400, detail="Provide scans or set smart=true")

    unknown = [s for s in scans_set if s not in reg]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown scans: {unknown}")

    # run scans sequentially for now (simple + predictable)
    results: dict[str, Any] = {}
    for scan_id in sorted(scans_set):
        res = await reg[scan_id].scan(req.target, False)
        results.update(res)

    findings = [f.to_dict() for f in normalize_findings(results, asset=req.target)]

    run_id = None
    if req.store:
        db_path = req.db or default_db_path()
        run_id = store_run(db_path, req.target, sorted(list(scans_set)), results, findings)

    return {"runId": run_id, "target": req.target, "scans": sorted(list(scans_set)), "results": results, "findings": findings}


@app.get("/runs")
def runs(limit: int = 20) -> dict[str, Any]:
    db_path = default_db_path()
    return {"runs": list_runs(db_path, limit=limit)}


@app.get("/runs/{run_id}")
def run_detail(run_id: int) -> dict[str, Any]:
    db_path = default_db_path()
    run = get_run(db_path, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run": run}


@app.get("/assets")
def assets(limit: int = 200) -> dict[str, Any]:
    db_path = default_assets_db_path()
    rows = [a.to_dict() for a in list_assets(db_path, limit=limit)]
    return {"assets": rows}
