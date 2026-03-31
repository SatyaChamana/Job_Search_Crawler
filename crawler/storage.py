import os
import logging
import threading
from datetime import datetime
from typing import List

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from crawler.parser_base import JobPosting

logger = logging.getLogger(__name__)

COLUMNS = [
    "Job ID",
    "Requisition ID",
    "Title",
    "Company",
    "Location",
    "Date Posted",
    "URL",
    "Added On",
]


class ExcelStorage:
    def __init__(self, filepath: str = "jobs.xlsx"):
        self.filepath = filepath
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self):
        """Create the Excel file with headers if it doesn't exist."""
        if os.path.exists(self.filepath):
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "Jobs"
        bold = Font(bold=True)
        for col_idx, header in enumerate(COLUMNS, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = bold
        wb.save(self.filepath)
        logger.info(f"Created new Excel file: {self.filepath}")

    def get_existing_dedup_keys(self) -> set:
        """Read all title|job_id dedup keys from the spreadsheet."""
        keys = set()
        wb = load_workbook(self.filepath, read_only=True)
        ws = wb.active
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row and row[0] is not None and row[2] is not None:
                job_id = str(row[0]).strip().lower()
                title = str(row[2]).strip().lower()
                keys.add(f"{title}|{job_id}")
        wb.close()
        return keys

    def add_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Deduplicate and append new jobs. Thread-safe. Returns list of newly added jobs."""
        with self._lock:
            existing_keys = self.get_existing_dedup_keys()
            new_jobs = [j for j in jobs if j.dedup_key not in existing_keys]

            if not new_jobs:
                logger.info("No new jobs to add.")
                return []

            wb = load_workbook(self.filepath)
            ws = wb.active
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for job in new_jobs:
                ws.append([
                    job.job_id,
                    job.requisition_id,
                    job.title,
                    job.company,
                    job.location,
                    job.date_posted,
                    job.url,
                    now,
                ])

            wb.save(self.filepath)
            logger.info(f"Added {len(new_jobs)} new jobs to {self.filepath}")
            return new_jobs

    def get_jobs_added_today_count(self) -> int:
        """Count jobs added today by checking the 'Added On' column (index 8)."""
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        count = 0
        with self._lock:
            wb = load_workbook(self.filepath, read_only=True)
            ws = wb.active
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and row[7] is not None and str(row[7]).startswith(today_prefix):
                    count += 1
            wb.close()
        return count
