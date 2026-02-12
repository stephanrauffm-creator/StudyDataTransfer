from __future__ import annotations

import fcntl
import logging
import os
import tempfile
from pathlib import Path

from django.conf import settings
from openpyxl import Workbook

from .models import AuditEvent, StudyEntry


audit_logger = logging.getLogger("study.audit")


class ExportLockError(Exception):
    pass


def write_audit_event(action: str, username: str, details: str = "") -> None:
    AuditEvent.objects.create(action=action, username=username, details=details)
    audit_logger.info("action=%s user=%s details=%s", action, username, details)


def export_entries_to_excel() -> str:
    target = Path(settings.DATA_XLSX_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)

    lock_path = target.with_suffix(target.suffix + ".lock")
    with lock_path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ExportLockError("Another export is in progress. Please try again.") from exc

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "StudyData"
        sheet.append(
            [
                "PIZ",
                "Examination Date",
                "Liver Ambulance Link",
                "Fibroscan LSM kPa",
                "Fibroscan CAP dBm",
                "Created At",
                "Updated At",
                "Created By",
                "Updated By",
            ]
        )

        for entry in StudyEntry.objects.select_related("created_by", "updated_by").order_by(
            "examination_date", "piz"
        ):
            sheet.append(
                [
                    entry.piz,
                    entry.examination_date.isoformat(),
                    "yes" if entry.liver_ambulance_link else "no",
                    float(entry.fibroscan_lsm_kpa),
                    float(entry.fibroscan_cap_dbm),
                    entry.created_at.isoformat(),
                    entry.updated_at.isoformat(),
                    entry.created_by.username if entry.created_by else "",
                    entry.updated_by.username if entry.updated_by else "",
                ]
            )

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".xlsx", dir=target.parent, delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)

        workbook.save(temp_path)
        os.replace(temp_path, target)

    return str(target)
