# FastAPI application: REST API and static dashboard UI for scrape jobs.
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.cli import argv_from_command_line, parse_args_for_api
from src.export import CSV_COLUMNS
from src.models import BusinessListing
from src.web.run_store import MAX_PAGES_CAP, RunStore, record_to_api_dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

RESULTS_SORT_FIELDS = frozenset(CSV_COLUMNS)
STATIC_DIR = PROJECT_ROOT / "static"
OUTPUT_ROOT = Path(os.environ.get("SCRAPER_OUTPUT_DIR", str(PROJECT_ROOT / "output")))

store = RunStore(OUTPUT_ROOT)

app = FastAPI(
    title="Local Business Directory Scraper",
    description="Dashboard API for Yellow Pages scrape jobs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateRunRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=200)
    max_pages: int = Field(1, ge=1, le=MAX_PAGES_CAP)
    export_csv: bool = True
    export_xlsx: bool = True


class CliRunRequest(BaseModel):
    command: str = Field(..., min_length=1, max_length=4000)
    export_csv: bool = True
    export_xlsx: bool = True


class DeleteRunsRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1, max_length=100)


class ResultRowPayload(BaseModel):
    company_name: str = ""
    website: str = ""
    phone: str = ""
    category: str = ""
    address: str = ""
    city: str = ""
    source_url: str = ""


class DeleteResultsRowsRequest(BaseModel):
    items: list[ResultRowPayload] = Field(..., min_length=1, max_length=500)


class ResultsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[dict[str, str]]


def _filter_companies(
    companies: list[BusinessListing],
    q: str,
    filter_city: str,
    filter_category: str,
    has_website: str,
):
    q_l = q.strip().lower()
    fc = filter_city.strip().lower()
    fcat = filter_category.strip().lower()
    result = []
    for c in companies:
        if q_l and q_l not in (c.company_name or "").lower():
            continue
        if fc and fc not in (c.city or "").lower():
            continue
        if fcat and fcat not in (c.category or "").lower():
            continue
        has_w = bool((c.website or "").strip())
        if has_website == "true" and not has_w:
            continue
        if has_website == "false" and has_w:
            continue
        result.append(c)
    return result


@app.post("/api/runs")
def api_create_run(body: CreateRunRequest):
    record = store.create_run(
        keyword=body.keyword,
        city=body.city,
        max_pages=body.max_pages,
        export_csv=body.export_csv,
        export_xlsx=body.export_xlsx,
    )
    return record_to_api_dict(record)


@app.post("/api/runs/cli")
def api_create_run_cli(body: CliRunRequest):
    argv = argv_from_command_line(body.command)
    if not argv:
        raise HTTPException(
            status_code=400,
            detail=(
                'Enter a command, e.g. python main.py --keyword plumber '
                '--city "Austin, TX" --max-pages 1'
            ),
        )
    try:
        parsed = parse_args_for_api(argv)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if parsed.max_pages > MAX_PAGES_CAP:
        raise HTTPException(
            status_code=400,
            detail=f"max_pages must be <= {MAX_PAGES_CAP} for dashboard runs.",
        )
    record = store.create_run(
        keyword=parsed.keyword.strip(),
        city=parsed.city.strip(),
        max_pages=parsed.max_pages,
        export_csv=body.export_csv,
        export_xlsx=body.export_xlsx,
    )
    return record_to_api_dict(record)


@app.get("/api/runs")
def api_list_runs(limit: int = Query(50, ge=1, le=100)):
    records = store.list_recent(limit=limit)
    return [record_to_api_dict(r) for r in records]


@app.post("/api/runs/delete")
def api_delete_runs(body: DeleteRunsRequest):
    unique_ids = list(dict.fromkeys(body.ids))
    return store.delete_runs(unique_ids)


@app.get("/api/runs/{run_id}")
def api_get_run(run_id: str):
    record = store.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return record_to_api_dict(record)


@app.get("/api/runs/{run_id}/results", response_model=ResultsResponse)
def api_get_results(
    run_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    sort: str = Query("company_name"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    q: str = "",
    filter_city: str = "",
    filter_category: str = "",
    has_website: str = Query("", pattern="^(|true|false)$"),
):
    record = store.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if sort not in RESULTS_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"sort must be one of: {', '.join(sorted(RESULTS_SORT_FIELDS))}",
        )
    filtered = _filter_companies(
        list(record.companies),
        q,
        filter_city,
        filter_category,
        has_website,
    )
    reverse = order == "desc"
    filtered.sort(
        key=lambda c: (getattr(c, sort) or "").lower(),
        reverse=reverse,
    )
    total = len(filtered)
    start = (page - 1) * per_page
    slice_rows = filtered[start : start + per_page]
    items = []
    for c in slice_rows:
        row = c.to_row()
        items.append({k: str(row.get(k, "") or "") for k in row})
    return ResultsResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=items,
    )


@app.post("/api/runs/{run_id}/results/delete")
def api_delete_results_rows(run_id: str, body: DeleteResultsRowsRequest):
    payload = [m.model_dump() for m in body.items]
    out = store.delete_result_rows(run_id, payload)
    if not out["found"]:
        raise HTTPException(status_code=404, detail="Run not found")
    if out.get("busy"):
        raise HTTPException(
            status_code=409,
            detail="Cannot delete rows while the run is queued or running.",
        )
    return {"removed": out["removed"]}


@app.get("/api/runs/{run_id}/download.csv")
def api_download_csv(run_id: str):
    record = store.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    path = store.run_dir(run_id) / "results.csv"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="CSV not available")
    return FileResponse(
        path,
        media_type="text/csv",
        filename=f"run-{run_id}.csv",
    )


@app.get("/api/runs/{run_id}/download.xlsx")
def api_download_xlsx(run_id: str):
    record = store.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    path = store.run_dir(run_id) / "results.xlsx"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Excel file not available")
    return FileResponse(
        path,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename=f"run-{run_id}.xlsx",
    )


@app.get("/")
def root():
    index = STATIC_DIR / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(status_code=404, detail="Dashboard not built (missing static/index.html)")


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
