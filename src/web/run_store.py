# In-memory run registry and background scrape execution for the dashboard API.
from __future__ import annotations

import logging
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.browser_client import YellowPagesBrowserClient
from src.dedupe import deduplicate_companies
from src.export import CSV_COLUMNS, export_companies_to_csv
from src.models import BusinessListing
from src.scraper import scrape_search_results
from src.xlsx_export import export_companies_to_xlsx

logger = logging.getLogger(__name__)

MAX_PAGES_CAP = 100


@dataclass
class RunRecord:
    id: str
    keyword: str
    city: str
    max_pages: int
    export_csv: bool
    export_xlsx: bool
    status: str
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    companies: list[BusinessListing] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error_message: str | None = None
    log_snippet: str = ""
    pages_total: int = 0
    pages_processed: int = 0
    pages_parsed_ok: int = 0
    pages_blocked: int = 0
    raw_records_count: int = 0
    unique_records_count: int = 0
    elapsed_seconds: float | None = None


def record_to_api_dict(record: RunRecord) -> dict:
    return {
        "id": record.id,
        "keyword": record.keyword,
        "city": record.city,
        "max_pages": record.max_pages,
        "export_csv": record.export_csv,
        "export_xlsx": record.export_xlsx,
        "status": record.status,
        "created_at": record.created_at,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "warnings": list(record.warnings),
        "error_message": record.error_message,
        "log_snippet": record.log_snippet,
        "pages_total": record.pages_total,
        "pages_processed": record.pages_processed,
        "pages_parsed_ok": record.pages_parsed_ok,
        "pages_blocked": record.pages_blocked,
        "raw_records_count": record.raw_records_count,
        "unique_records_count": record.unique_records_count,
        "elapsed_seconds": record.elapsed_seconds,
    }


class RunStore:
    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root
        self._lock = threading.Lock()
        self._runs: dict[str, RunRecord] = {}

    def create_run(
        self,
        *,
        keyword: str,
        city: str,
        max_pages: int,
        export_csv: bool,
        export_xlsx: bool,
    ) -> RunRecord:
        run_id = uuid.uuid4().hex
        record = RunRecord(
            id=run_id,
            keyword=keyword.strip(),
            city=city.strip(),
            max_pages=max_pages,
            export_csv=export_csv,
            export_xlsx=export_xlsx,
            status="queued",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._runs[run_id] = record
        threading.Thread(target=self._execute, args=(run_id,), daemon=True).start()
        return record

    def get(self, run_id: str) -> RunRecord | None:
        with self._lock:
            return self._runs.get(run_id)

    def list_recent(self, *, limit: int) -> list[RunRecord]:
        with self._lock:
            items = list(self._runs.values())
        items.sort(key=lambda r: r.created_at or "", reverse=True)
        return items[:limit]

    def delete_runs(self, run_ids: list[str]) -> dict[str, list[str]]:
        """Remove finished runs from memory and delete their output folders.

        Skips unknown ids and runs that are still ``queued`` or ``running``.
        """
        to_remove: list[str] = []
        skipped: list[str] = []
        with self._lock:
            for rid in run_ids:
                if rid not in self._runs:
                    skipped.append(rid)
                    continue
                rec = self._runs[rid]
                if rec.status in ("running", "queued"):
                    skipped.append(rid)
                    continue
                del self._runs[rid]
                to_remove.append(rid)
        for rid in to_remove:
            path = self.run_dir(rid)
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
        return {"deleted": to_remove, "skipped": skipped}

    def _company_row_key(self, c: BusinessListing) -> tuple[str, ...]:
        row = c.to_row()
        return tuple(str(row.get(k, "") or "").strip().lower() for k in CSV_COLUMNS)

    def _row_key_from_payload(self, item: dict[str, str]) -> tuple[str, ...]:
        return tuple(str(item.get(k, "") or "").strip().lower() for k in CSV_COLUMNS)

    def delete_result_rows(
        self, run_id: str, items: list[dict[str, str]]
    ) -> dict[str, int | bool]:
        """Remove listings whose fields match any payload row (case-insensitive trim)."""
        keys_to_remove = {self._row_key_from_payload(it) for it in items}
        with self._lock:
            record = self._runs.get(run_id)
            if record is None:
                return {"removed": 0, "found": False, "busy": False}
            if record.status in ("running", "queued"):
                return {"removed": 0, "found": True, "busy": True}
            before = len(record.companies)
            record.companies = [
                c
                for c in record.companies
                if self._company_row_key(c) not in keys_to_remove
            ]
            removed = before - len(record.companies)
            record.unique_records_count = len(record.companies)
            export_csv = record.export_csv
            export_xlsx = record.export_xlsx
            companies_copy = list(record.companies)

        run_path = self.run_dir(run_id)
        if export_csv:
            csv_path = run_path / "results.csv"
            if companies_copy:
                export_companies_to_csv(companies_copy, csv_path)
            elif csv_path.is_file():
                csv_path.unlink(missing_ok=True)
        if export_xlsx:
            xlsx_path = run_path / "results.xlsx"
            if companies_copy:
                export_companies_to_xlsx(companies_copy, xlsx_path)
            elif xlsx_path.is_file():
                xlsx_path.unlink(missing_ok=True)

        return {"removed": removed, "found": True, "busy": False}

    def run_dir(self, run_id: str) -> Path:
        return self.output_root / "runs" / run_id

    def _execute(self, run_id: str) -> None:
        with self._lock:
            record = self._runs.get(run_id)
        if record is None:
            return

        run_path = self.run_dir(run_id)
        run_path.mkdir(parents=True, exist_ok=True)
        t0 = time.perf_counter()
        try:
            with self._lock:
                record.status = "running"
                record.started_at = datetime.now(timezone.utc).isoformat()

            client = YellowPagesBrowserClient(headless=True)
            result = scrape_search_results(
                client=client,
                keyword=record.keyword,
                city=record.city,
                max_pages=record.max_pages,
                output_dir=run_path,
            )
            raw = result.companies
            unique = deduplicate_companies(raw)
            pages_blocked = sum(1 for p in result.pages if p.status == "blocked")
            pages_ok = sum(1 for p in result.pages if p.status == "ok")

            warnings: list[str] = []
            if pages_blocked:
                warnings.append(
                    f"{pages_blocked} page(s) returned blocked content (no listings parsed)."
                )

            if record.export_csv:
                export_companies_to_csv(unique, run_path / "results.csv")
            if record.export_xlsx:
                export_companies_to_xlsx(unique, run_path / "results.xlsx")

            elapsed = time.perf_counter() - t0
            log_tail = (
                f"Done: {len(unique)} unique from {len(raw)} raw rows, "
                f"{pages_ok} ok / {len(result.pages)} pages."
            )
            with self._lock:
                record.companies = unique
                record.raw_records_count = len(raw)
                record.unique_records_count = len(unique)
                record.pages_total = record.max_pages
                record.pages_processed = len(result.pages)
                record.pages_parsed_ok = pages_ok
                record.pages_blocked = pages_blocked
                record.warnings = warnings
                record.status = (
                    "completed_with_warnings" if warnings else "completed"
                )
                record.finished_at = datetime.now(timezone.utc).isoformat()
                record.elapsed_seconds = round(elapsed, 2)
                record.log_snippet = log_tail
        except Exception as exc:
            logger.exception("Run %s failed", run_id)
            elapsed = time.perf_counter() - t0
            with self._lock:
                record.status = "failed"
                record.error_message = str(exc)
                record.finished_at = datetime.now(timezone.utc).isoformat()
                record.elapsed_seconds = round(elapsed, 2)
                record.log_snippet = str(exc)[:2000]
