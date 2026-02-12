from __future__ import annotations

import contextlib
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


@contextlib.contextmanager
def advisory_export_lock(lock_path: str):
    lock_file_path = Path(lock_path)
    lock_file_path.parent.mkdir(parents=True, exist_ok=True)

    lock_file = lock_file_path.open("a+b")
    lock_acquired = False
    platform_lock = None

    try:
        try:
            import fcntl  # type: ignore

            platform_lock = "fcntl"
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_acquired = True
        except ImportError:
            import msvcrt  # type: ignore

            platform_lock = "msvcrt"
            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"0")
                lock_file.flush()
            lock_file.seek(0)
            try:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                lock_acquired = True
            except OSError as exc:
                raise ExportLockError("Export in progress, try again later") from exc
        yield
    except ExportLockError:
        raise
    except OSError as exc:
        if not lock_acquired:
            raise ExportLockError("Export in progress, try again later") from exc
        raise
    finally:
        if lock_acquired:
            if platform_lock == "fcntl":
                import fcntl  # type: ignore

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            elif platform_lock == "msvcrt":
                import msvcrt  # type: ignore

                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        lock_file.close()


def write_audit_event(action: str, username: str, details: str = "") -> None:
    AuditEvent.objects.create(action=action, username=username, details=details)
    audit_logger.info("action=%s user=%s details=%s", action, username, details)


def export_entries_to_excel() -> str:
    target = Path(settings.DATA_XLSX_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)

    lock_path = f"{target}.lock"
    with advisory_export_lock(lock_path):
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
