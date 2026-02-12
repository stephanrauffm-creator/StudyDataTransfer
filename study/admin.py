from django.contrib import admin

from .models import AuditEvent, StudyEntry, StudyInstruction


@admin.register(StudyEntry)
class StudyEntryAdmin(admin.ModelAdmin):
    list_display = (
        "piz",
        "examination_date",
        "liver_ambulance_link",
        "fibroscan_lsm_kpa",
        "fibroscan_cap_dbm",
        "created_at",
    )
    search_fields = ("piz",)
    list_filter = ("examination_date", "liver_ambulance_link")


@admin.register(StudyInstruction)
class StudyInstructionAdmin(admin.ModelAdmin):
    list_display = ("title", "uploaded_at", "uploaded_by")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("action", "username", "created_at")
    readonly_fields = ("action", "username", "details", "created_at")
