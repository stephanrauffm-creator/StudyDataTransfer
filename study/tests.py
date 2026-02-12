from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import StudyEntry


class StudyEntryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="alice", password="pw12345")

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
