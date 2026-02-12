from __future__ import annotations

import logging
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from django.conf import settings
from openpyxl import Workbook

from .models import AuditEvent, StudyEntry


audit_logger = logging.getLogger("study.audit")

try:
    import fcntl
except ImportError:  # pragma: no cover - platform-specific
    fcntl = None

try:
    import msvcrt
except ImportError:  # pragma: no cover - platform-specific
    msvcrt = None


class ExportLockError(Exception):
    pass


@contextmanager
def advisory_export_lock(lock_path: str):
    lock_file_path = Path(lock_path)
    lock_file_path.parent.mkdir(parents=True, exist_ok=True)

    with lock_file_path.open("a+b") as lock_file:
        if msvcrt is not None and lock_file.tell() == 0:
            lock_file.write(b"0")
            lock_file.flush()

        if fcntl is not None:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ExportLockError("Export in progress, try again later") from exc
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            return

        if msvcrt is not None:
            lock_file.seek(0)
            try:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise ExportLockError("Export in progress, try again later") from exc
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            return

        raise ExportLockError("Export locking is unavailable on this platform")


def write_audit_event(action: str, username: str, details: str = "") -> None:
    AuditEvent.objects.create(action=action, username=username, details=details)
    audit_logger.info("action=%s user=%s details=%s", action, username, details)


def export_entries_to_excel() -> str:
    target = Path(settings.DATA_XLSX_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)

    lock_path = target.with_suffix(target.suffix + ".lock")
    with advisory_export_lock(str(lock_path)):
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
