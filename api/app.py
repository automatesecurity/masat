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
from utils.history import default_db_path, store_run, list_runs


app = FastAPI(title="MASAT API", version="0.1")


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

    findings = [f.to_dict() for f in normalize_findings(results)]

    run_id = None
    if req.store:
        db_path = req.db or default_db_path()
        run_id = store_run(db_path, req.target, sorted(list(scans_set)), results, findings)

    return {"runId": run_id, "target": req.target, "scans": sorted(list(scans_set)), "results": results, "findings": findings}


@app.get("/runs")
def runs(limit: int = 20, db: str | None = None) -> dict[str, Any]:
    db_path = db or default_db_path()
    return {"runs": list_runs(db_path, limit=limit)}
