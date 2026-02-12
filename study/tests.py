from datetime import date
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import StudyEntry


class StudyEntryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alice", password="pw12345")
        self.other_user = get_user_model().objects.create_user(username="bob", password="pw12345")
        self.staff_user = get_user_model().objects.create_user(
            username="admin", password="pw12345", is_staff=True
        )

    def test_authenticated_access_required(self):
        response = self.client.get(reverse("entry-list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_create_entry(self):
        self.client.login(username="alice", password="pw12345")
        response = self.client.post(
            reverse("entry-create"),
            {
                "piz": "PIZ001",
                "examination_date": "2024-01-01",
                "liver_ambulance_link": True,
                "fibroscan_lsm_kpa": "8.5",
                "fibroscan_cap_dbm": "240.0",
            },
        )
        self.assertEqual(response.status_code, 302)
        entry = StudyEntry.objects.get(piz="PIZ001")
        self.assertEqual(entry.created_by, self.user)

    def test_unique_constraint(self):
        StudyEntry.objects.create(
            piz="PIZ001",
            examination_date=date(2024, 1, 1),
            liver_ambulance_link=False,
            fibroscan_lsm_kpa="5.1",
            fibroscan_cap_dbm="100.0",
            created_by=self.user,
            updated_by=self.user,
        )
        with self.assertRaises(IntegrityError):
            StudyEntry.objects.create(
                piz="PIZ001",
                examination_date=date(2024, 1, 1),
                liver_ambulance_link=False,
                fibroscan_lsm_kpa="5.1",
                fibroscan_cap_dbm="100.0",
                created_by=self.user,
                updated_by=self.user,
            )

    def test_export_endpoint_returns_xlsx(self):
        self.client.login(username="alice", password="pw12345")
        StudyEntry.objects.create(
            piz="PIZ002",
            examination_date=date(2024, 1, 2),
            liver_ambulance_link=True,
            fibroscan_lsm_kpa="12.4",
            fibroscan_cap_dbm="301.0",
            created_by=self.user,
            updated_by=self.user,
        )
        response = self.client.get(reverse("export-excel"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_non_creator_non_staff_cannot_edit_entry(self):
        entry = StudyEntry.objects.create(
            piz="PIZ003",
            examination_date=date(2024, 1, 3),
            liver_ambulance_link=False,
            fibroscan_lsm_kpa="6.5",
            fibroscan_cap_dbm="230.0",
            created_by=self.user,
            updated_by=self.user,
        )
        self.client.login(username="bob", password="pw12345")
        response = self.client.post(
            reverse("entry-edit", kwargs={"pk": entry.pk}),
            {
                "piz": entry.piz,
                "examination_date": entry.examination_date.isoformat(),
                "liver_ambulance_link": entry.liver_ambulance_link,
                "fibroscan_lsm_kpa": entry.fibroscan_lsm_kpa,
                "fibroscan_cap_dbm": entry.fibroscan_cap_dbm,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_non_staff_cannot_upload_instruction(self):
        self.client.login(username="alice", password="pw12345")
        response = self.client.get(reverse("instruction-upload"))
        self.assertEqual(response.status_code, 403)

    def test_staff_can_access_upload_instruction(self):
        self.client.login(username="admin", password="pw12345")
        response = self.client.get(reverse("instruction-upload"))
        self.assertEqual(response.status_code, 200)


class ServicesImportTests(TestCase):
    def test_services_import_works_without_fcntl(self):
        import importlib
        import sys

        sys.modules.pop("study.services", None)
        real_import = __import__

        def mocked_import(name, *args, **kwargs):
            if name == "fcntl":
                raise ImportError("simulated for windows")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=mocked_import):
            module = importlib.import_module("study.services")

        self.assertTrue(hasattr(module, "export_entries_to_excel"))
        sys.modules.pop("study.services", None)
