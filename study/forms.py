from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import StudyEntry, StudyInstruction


class StudyEntryForm(forms.ModelForm):
    class Meta:
        model = StudyEntry
        fields = [
            "piz",
            "examination_date",
            "liver_ambulance_link",
            "fibroscan_lsm_kpa",
            "fibroscan_cap_dbm",
        ]
        widgets = {
            "examination_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_examination_date(self):
        exam_date = self.cleaned_data["examination_date"]
        if exam_date > timezone.now().date() + timedelta(days=30):
            raise forms.ValidationError("Examination date cannot be more than 30 days in the future.")
        return exam_date

    def clean_fibroscan_lsm_kpa(self):
        value = self.cleaned_data["fibroscan_lsm_kpa"]
        if value < 0 or value > 120:
            raise forms.ValidationError("LSM kPa must be between 0 and 120.")
        return value

    def clean_fibroscan_cap_dbm(self):
        value = self.cleaned_data["fibroscan_cap_dbm"]
        if value < 0 or value > 500:
            raise forms.ValidationError("CAP dBm must be between 0 and 500.")
        return value


class StudyInstructionForm(forms.ModelForm):
    class Meta:
        model = StudyInstruction
        fields = ["title", "pdf"]

    def clean_pdf(self):
        file_obj = self.cleaned_data["pdf"]
        if not file_obj.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Only PDF files are allowed.")
        return file_obj
