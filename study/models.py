from django.conf import settings
from django.db import models


class StudyEntry(models.Model):
    piz = models.CharField(max_length=128)
    examination_date = models.DateField()
    liver_ambulance_link = models.BooleanField(default=False)
    fibroscan_lsm_kpa = models.DecimalField(max_digits=6, decimal_places=2)
    fibroscan_cap_dbm = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="study_entries_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="study_entries_updated",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["piz", "examination_date"], name="unique_piz_exam_date"
            )
        ]
        ordering = ["-examination_date", "piz"]

    def __str__(self) -> str:
        return f"{self.piz} - {self.examination_date}"


class StudyInstruction(models.Model):
    title = models.CharField(max_length=255)
    pdf = models.FileField(upload_to="instructions/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="study_instructions_uploaded",
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.title


class AuditEvent(models.Model):
    action = models.CharField(max_length=64)
    username = models.CharField(max_length=150)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.created_at} {self.action}"
