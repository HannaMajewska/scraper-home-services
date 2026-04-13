# Excel export for business listings (dashboard downloads).
from pathlib import Path

from openpyxl import Workbook

from src.export import CSV_COLUMNS
from src.models import BusinessListing


def export_companies_to_xlsx(
    companies: list[BusinessListing],
    xlsx_path: Path,
) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(CSV_COLUMNS)
    for company in companies:
        row = company.to_row()
        worksheet.append([str(row.get(column, "") or "").strip() for column in CSV_COLUMNS])
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(xlsx_path)
